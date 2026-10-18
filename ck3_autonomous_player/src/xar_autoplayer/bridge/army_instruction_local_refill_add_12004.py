"""Strict native hardware ADD wire consumer; no process access or evaluation.

The caller owns the fresh process/cohort/build/SYSTEM admission whose pins are
retained in binding. Matching those identifiers does not prove a native parent,
date, complete window, toggle effect, or the source of a prior core NET record.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import PureWindowsPath
import re
import struct

EXE_SHA256 = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
RAW_SCHEMA = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v2'
BINDING_SCHEMA = 'xar.ck3.refill_ADD_12004.owner_binding.v1'
ITEM_SCHEMA = 'xar.ck3.refill_ADD_12004.instruction_item.v1'


def _need(ok: bool, message: str) -> None:
    if not ok: raise ValueError(message)


def _int(x: object, lo: int = 0, hi: int = (1 << 64) - 1) -> bool:
    return type(x) is int and lo <= x <= hi


def _address(x: object) -> int:
    _need(type(x) is str and re.fullmatch(r'0x[0-9A-F]+', x) is not None, 'native address encoding')
    n = int(x, 16); _need(0 < n < (1 << 64), 'nonzero native address'); return n


def _i32(x: int) -> int:
    return struct.unpack('<i', struct.pack('<I', x))[0]


def _normalize_instruction_local_refill_add_v2_12004(raw: bytes, binding: Mapping[str, object], *,
                                                       _native_campaign_null: bool = False) -> dict[str, object]:
    """Normalize exactly one selected native ADD after the owner verified admission.

    Binding contains actual owner evidence hashes, not self-asserted success flags.
    Its freshness/authority is external and remains explicitly outside this reader.
    Controlled synthetic native wire is always rejected, even if fixture is relabeled.
    """
    _need(type(raw) is bytes and 0 < len(raw) <= 131072, 'bounded immutable native NDJSON')
    fields = {'schema', 'machine_id', 'exact_executable_sha256', 'pid', 'process_created_filetime',
              'thread_id', 'regi_full_id_u32', 'physical_slot', 'arrg_full_id_i32', 'army_full_id_i32',
              'connection_generation', 'episode_run_id', 'source_admission_receipt_sha256',
              'observer_build_and_SYSTEM_gate_receipt_sha256'}
    _need(isinstance(binding, Mapping) and set(binding) == fields and binding['schema'] == BINDING_SCHEMA,
          'exact owner binding schema')
    _need(binding['exact_executable_sha256'] == EXE_SHA256 and type(binding['machine_id']) is str and
          re.fullmatch(r'[a-z0-9-]{1,128}', binding['machine_id']) is not None, 'machine/exact4 source identity')
    for key in ('pid', 'thread_id'):
        _need(_int(binding[key], 1, 0xFFFFFFFF), 'owner '+key)
    for key in ('process_created_filetime', 'connection_generation'):
        _need(_int(binding[key], 1), 'owner '+key)
    if _native_campaign_null:
        _need(binding['episode_run_id'] is None, 'ordinary owner preserves null game episode')
    else:
        _need(type(binding['episode_run_id']) is str and 0 < len(binding['episode_run_id']) <= 256, 'owner episode')
    _need(_int(binding['regi_full_id_u32'], 0, 0xFFFFFFFE) and _int(binding['physical_slot'], 0, 6), 'selected full Regi/physical slot')
    for key in ('arrg_full_id_i32', 'army_full_id_i32'):
        _need(_int(binding[key], -(1 << 31), (1 << 31)-1) and binding[key] != -1, 'selected full '+key)
    for key in ('source_admission_receipt_sha256', 'observer_build_and_SYSTEM_gate_receipt_sha256'):
        _need(type(binding[key]) is str and re.fullmatch(r'[0-9a-f]{64}', binding[key]) is not None, 'actual owner evidence pin')
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    _need(len(rows) == 6 and all(type(row) is dict for row in rows), 'complete native six-row capture')
    _need([row.get('kind') for row in rows] == ['start', 'raw_ADD_boundary', 'raw_ADD_boundary',
          'physical_ADD_pair', 'debug_hit_budget', 'terminal'], 'native order/source kind; no fixture or NET projection')
    start, a, b, pair, budget, terminal = rows
    start_keys = {'kind','schema','machine_id','exact_exe_sha256_basis','pid','process_created_filetime',
                  'module_base','fixture','thread_id','regi_full_id_u32','physical_slot','timeout_ms',
                  'verified_site_0_hex','verified_site_1_hex'}
    _need(set(start) == start_keys and start['schema'] == RAW_SCHEMA and start['fixture'] is False and
          start['exact_exe_sha256_basis'] == 'external-frozen-runtime-admission', 'native production source; synthetic forbidden')
    _need(start['verified_site_0_hex'] == '0150f4' and start['verified_site_1_hex'] == '8b48f43b48f0', 'actual guarded9B readback')
    base = _address(start['module_base']); _need(base <= (1 << 64)-1-0x61C5000, 'module image overflow')
    _need(_int(start['timeout_ms'], 1000, 300000), 'finite observation timeout')
    for key in ('machine_id','pid','process_created_filetime','thread_id','regi_full_id_u32','physical_slot'):
        _need(type(start[key]) is type(binding[key]) and start[key] == binding[key], 'start owner match '+key)
    identity = ('pid','thread_id','regi_pointer','regi_full_id_u32','physical_slot','rax_anchor','rsp','core_caller_raw',
                'manager_iterator','q_index','q_u32','q_i32','maximum_u32','arrg_raw','arrg_resolved','arrg_pointer',
                'army_raw','army_resolved','data_count','DATA')
    _need(all(a.get(k) == b.get(k) and type(a.get(k)) is type(b.get(k)) for k in identity), 'same physical ADD occurrence')
    hit_keys = {'kind','machine_id','site_rva','pid','thread_id','event_ordinal','debug_event_ordinal','qpc',
                'regi_pointer','regi_full_id_u32','physical_slot','rax_anchor','rsp','core_caller_raw','manager_iterator',
                'q_index','q_u32','q_i32','current_u32','maximum_u32','physical_complete','native_core_token',
                'natural_parent_token','natural_attribution_ready','arrg_raw','arrg_resolved','arrg_pointer',
                'army_raw','army_resolved','data_count','associated_ArRg_DATA_complete','DATA','physical_seven_hex'}
    for i, hit in enumerate((a, b)):
        _need(set(hit) == hit_keys, 'exact native boundary; no fixture address/source alias')
        _need(hit['site_rva'] == ('0x2A98B88','0x2A98B8B')[i] and _int(hit['event_ordinal'], i+1, i+1), 'actual pre/post PCs and retained order')
        _need(hit['machine_id'] == binding['machine_id'] and all(type(hit[k]) is type(binding[k]) and hit[k] == binding[k]
              for k in ('pid','thread_id','regi_full_id_u32','physical_slot')), 'selected native identities')
        _need(hit['physical_complete'] is True and hit['associated_ArRg_DATA_complete'] is True, 'complete physical/DATA capture')
        _need(hit['native_core_token'] is None and hit['natural_parent_token'] is None and hit['natural_attribution_ready'] is False, 'no invented native parent')
        for key in ('q_u32','current_u32','maximum_u32'):
            _need(_int(hit[key], 0, 0xFFFFFFFF), 'raw DWORD '+key)
        _need(_int(hit['q_i32'], -(1 << 31), (1 << 31)-1) and hit['q_i32'] == _i32(hit['q_u32']), 'signed operand bits')
        _need(_int(hit['q_index'], -(1 << 31), (1 << 31)-1), 'raw q-index')
        _need(_int(hit['qpc'], 1) and _int(hit['debug_event_ordinal'], 1, 100000), 'native counter/order')
        _need(_address(hit['rax_anchor']) == _address(hit['regi_pointer']) + 0x28 + hit['physical_slot']*0x24, 'actual physical slot address')
        for key in ('rsp','core_caller_raw','manager_iterator','arrg_pointer'): _address(hit[key])
        for raw_key, expected_key in (('arrg_raw','arrg_full_id_i32'),('arrg_resolved','arrg_full_id_i32'),
                                      ('army_raw','army_full_id_i32'),('army_resolved','army_full_id_i32')):
            _need(type(hit[raw_key]) is int and hit[raw_key] == binding[expected_key], 'full-generation DATA/Army owner')
        data = hit['DATA']; _need(type(data) is list and _int(hit['data_count'], 1, 64) and len(data) == hit['data_count'], 'whole associated DATA count')
        for j, record in enumerate(data):
            _need(type(record) is dict and set(record) == {'stored_index','raw0','raw4','persistent_full_id_u32','physical_ordinal_u32'} and
                  _int(record['stored_index'], j, j) and all(_int(record[k], 0, 0xFFFFFFFF) for k in
                  ('raw0','raw4','persistent_full_id_u32','physical_ordinal_u32')), 'raw DATA order/width')
        _need(any(r['persistent_full_id_u32'] == binding['regi_full_id_u32'] and r['physical_ordinal_u32'] == binding['physical_slot'] for r in data), 'selected DATA alias exists')
        _need(type(hit['physical_seven_hex']) is str and re.fullmatch(r'[0-9a-f]{504}', hit['physical_seven_hex']) is not None, 'complete252B physical copy')
    _need(a['qpc'] < b['qpc'] and b['debug_event_ordinal'] == a['debug_event_ordinal']+1, 'adjacent actual hardware trap sequence')
    before, after = (bytes.fromhex(h['physical_seven_hex']) for h in (a,b));offset = a['physical_slot']*0x24+4
    for hit, seven in ((a,before),(b,after)):
        _need(struct.unpack_from('<I',seven,offset)[0] == hit['current_u32'] and
              struct.unpack_from('<I',seven,offset-4)[0] == hit['maximum_u32'] and
              struct.unpack_from('<i',seven,offset+8)[0] == hit['q_index'] and
              struct.unpack_from('<i',seven,offset+12)[0] == hit['arrg_raw'], 'raw seven scalar agreement')
    _need(before[:offset] == after[:offset] and before[offset+4:] == after[offset+4:] and
          (a['current_u32']+a['q_u32']) & 0xFFFFFFFF == b['current_u32'], 'one DWORD modular ADD')
    pair_keys = {'kind','machine_id','actual_ADD_observed','native_instruction_replayed_by_probe','q_i32',
                 'before_current_u32','after_current_u32','DWORD_wrap_matches','associated_DATA_pair_complete',
                 'natural_parent_token','natural_attribution_ready','full_window_coverage_ready'}
    _need(set(pair) == pair_keys and type(pair['q_i32']) is int and type(pair['before_current_u32']) is int and
          type(pair['after_current_u32']) is int and pair.get('machine_id') == binding['machine_id'] and pair.get('actual_ADD_observed') is True and
          pair.get('native_instruction_replayed_by_probe') is False and pair.get('DWORD_wrap_matches') is True and
          pair.get('associated_DATA_pair_complete') is True and pair.get('q_i32') == a['q_i32'] and
          pair.get('before_current_u32') == a['current_u32'] and pair.get('after_current_u32') == b['current_u32'] and
          pair.get('natural_parent_token') is None and pair.get('natural_attribution_ready') is False and
          pair.get('full_window_coverage_ready') is False and 'fixture' not in pair and 'CK3_actual_ADD_observed' not in pair,
          'native pair declaration agrees; no synthetic promotion')
    _need(terminal == {'kind':'terminal','status':'paired','reason':'paired','debug_registers_cleared':True,'detached':True,'hit_count':2} and
          terminal['debug_registers_cleared'] is True and terminal['detached'] is True and type(terminal['hit_count']) is int, 'actual cleanup/restore/detach')
    _need(set(budget) == {'kind','debug_hits','limit'} and _int(budget['limit'],100000,100000) and
          _int(budget['debug_hits'], b['debug_event_ordinal'],100000), 'finite total trap budget')
    aliases = sum(r['persistent_full_id_u32'] == binding['regi_full_id_u32'] and r['physical_ordinal_u32'] == binding['physical_slot'] for r in a['DATA'])
    return {'schema':ITEM_SCHEMA,'source_kind':'native_instruction_local_physical_ADD','raw_sha256':hashlib.sha256(raw).hexdigest(),
            'owner_binding':dict(binding),'owner_admission_authority_verified_here':False,
            'actual_ADD_observed':True,'instruction_operand_signed32':a['q_i32'],'instruction_operand_u32':a['q_u32'],
            'before_current_u32':a['current_u32'],'after_current_u32':b['current_u32'],
            'signed_endpoint_net':_i32(b['current_u32'])-_i32(a['current_u32']),
            'unsigned_endpoint_net':b['current_u32']-a['current_u32'],'DWORD_wrap_matches':True,
            'regi_full_id_u32':a['regi_full_id_u32'],'physical_slot':a['physical_slot'],
            'arrg_full_id_i32':a['arrg_resolved'],'army_full_id_i32':a['army_resolved'],
            'DATA':a['DATA'],'matching_DATA_aliases':aliases,'physical_seven_before_hex':a['physical_seven_hex'],
            'physical_seven_after_hex':b['physical_seven_hex'],'debug_hits':budget['debug_hits'],
            'clean_detach_and_register_restore':True,'instruction_replayed_by_probe':False,
            'natural_parent_token':None,'native_core_token':None,'native_event_date_raw':None,
            'same_core_NET_cause_proven':False,'natural_attribution_ready':False,'full_window_coverage_ready':False,
            'toggle_effect_proven':False,'refill_business_qualification_granted':False}


def _normalize_stack_q_source_v3_12004(raw: bytes, binding: Mapping[str, object], *,
                                     _native_campaign_null: bool = False) -> dict[str, object]:
    """Validate extra actual B84 load evidence, then reuse every v2 ADD guard.

    The 28-byte window is an independently read native stack copy. Its selected
    DWORD is the already capped instruction operand, not an uncapped request or
    a per-Army sum. Physical slot and q-index are separate domains.
    """
    _need(type(raw) is bytes and 0 < len(raw) <= 131072, 'bounded v3 wire')
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    _need(len(rows) == 6 and all(type(row) is dict for row in rows), 'v3 six native rows')
    _need(rows[0].get('schema') == 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3', 'exact v3 source')
    windows = []
    for hit in rows[1:3]:
        _need(hit.get('stack_q_source_complete') is True, 'actual bounded stack q capture')
        window = hit.get('stack_q_window_28_hex')
        _need(type(window) is str and re.fullmatch(r'[0-9a-f]{56}', window) is not None,
              'exact 28-byte stack q window')
        _need(_int(hit.get('q_index'), 0, 6), 'collected q-index inside stack window')
        selected = struct.unpack_from('<I', bytes.fromhex(window), 4*hit['q_index'])[0]
        _need(type(hit.get('q_u32')) is int and selected == hit['q_u32'], 'B84 stack slot equals actual EDX')
        windows.append(window)
    _need(windows[0] == windows[1], 'independent stack q windows unchanged across one ADD')
    # Strip only the two newly verified fields. Unknown/synthetic fields still
    # reach v2's exact-key check and fail; this is no fallback from a bad v3 row.
    rows[0]['schema'] = RAW_SCHEMA
    for hit in rows[1:3]:
        del hit['stack_q_source_complete']; del hit['stack_q_window_28_hex']
    projection = ('\n'.join(json.dumps(row, separators=(',', ':')) for row in rows)+'\n').encode()
    item = _normalize_instruction_local_refill_add_v2_12004(
        projection, binding, _native_campaign_null=_native_campaign_null)
    item['raw_sha256'] = hashlib.sha256(raw).hexdigest()
    item['raw_schema'] = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
    item['instruction_stack_q_source_v1'] = {
        'status': 'available', 'load_rva': '0x2A98B84', 'ADD_rva': '0x2A98B88',
        'q_index': rows[1]['q_index'], 'stack_window_before_hex': windows[0],
        'stack_window_after_hex': windows[1], 'stack_selected_u32': rows[1]['q_u32'],
        'source_path': 'request_return_nonzero_then_physical_seven_loop',
        'source_path_basis': 'exact4_PC_control_flow_inference',
        'request_call_rva': '0x2A98B53', 'request_target_rva': '0x262C9B0',
        'request_gate_rva': '0x2A98B5F', 'physical_slot_equals_q_index_required': False,
        'uncapped_request_observed': False, 'individual_permission_branches_observed': False,
    }
    return item


_CARRIER_EPOCH = 20261018
_CARRIER_WORDS = (
    'sequence', 'owner_tid', 'active', 'invocation_token', 'parent_invocation_token',
    'nesting_depth', 'core_clock_identity', 'core_entry_sequence', 'core_thread_id',
    'natural_clock_identity', 'natural_entry_sequence', 'natural_thread_id',
    'date_raw', 'manager_identity', 'secondary_manager_identity', 'game_state_identity',
    'caller_return_rva', 'natural_entry_rva', 'entry_provenance_complete',
    'saved_mask02_admitted', 'invocation_kind',
)
_CARRIER_HEADER_HEX = struct.pack('<8Q', 0x3152303643524158, 1, _CARRIER_EPOCH,
                                  16, 21, 8, 0x98702F88A547CDE2, 0).hex()
_V4_SCHEMA = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v4'
_BINDING_V2_SCHEMA = 'xar.ck3.refill_ADD_12004.owner_binding.v2'
_BINDING_V3_SCHEMA = 'xar.ck3.refill_ADD_12004.owner_binding.v3'


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        _need(key not in result, 'duplicate native JSON field')
        result[key] = value
    return result


def _carrier_frame(hit: dict, start: dict, binding: Mapping[str, object]) -> dict:
    carrier = hit.get('core_carrier_v1')
    fields = {'module_path', 'module_base', 'export_rva', 'directory_address',
              'source_epoch', 'header_64_hex', 'slot_index', 'slot_address',
              'first_168_hex', 'second_168_hex', 'stable_active', 'frame',
              'owners_complete', 'owner_matches', 'header_complete',
              'first_complete', 'second_complete', 'diagnostic'}
    _need(type(carrier) is dict and set(carrier) == fields, 'exact actual core carrier snapshot')
    for key in ('module_path', 'module_base', 'export_rva', 'source_epoch', 'header_64_hex'):
        _need(type(carrier[key]) is type(start['carrier_' + key]) and
              carrier[key] == start['carrier_' + key], 'carrier/start agreement ' + key)
    _need(carrier['directory_address'] == start['carrier_address'], 'carrier directory/start agreement')
    _need(carrier['stable_active'] is True, 'independently stable active carrier required')
    _need(all(carrier[key] is True for key in ('owners_complete', 'header_complete',
          'first_complete', 'second_complete')) and _int(carrier['owner_matches'], 1, 1) and
          carrier['diagnostic'] == 'stable_active', 'actual complete unambiguous carrier reader diagnostics')
    _need(_int(carrier['slot_index'], 0, 15), 'actual carrier slot index')
    address = _address(carrier['directory_address'])
    _need(address <= (1 << 64) - 1 - (64 + 16 * 168), 'carrier directory extent overflow')
    _need(_address(carrier['slot_address']) == address + 64 + carrier['slot_index'] * 168,
          'actual carrier slot address')
    for key in ('first_168_hex', 'second_168_hex'):
        _need(type(carrier[key]) is str and re.fullmatch(r'[0-9a-f]{336}', carrier[key]) is not None,
              'complete 168-byte carrier read')
    _need(carrier['first_168_hex'] == carrier['second_168_hex'], 'carrier double snapshot fence mismatch')
    frame = carrier['frame']
    _need(type(frame) is dict and set(frame) == set(_CARRIER_WORDS) and
          all(_int(frame[name]) for name in _CARRIER_WORDS), 'exact 21 unsigned carrier words')
    actual = dict(zip(_CARRIER_WORDS, struct.unpack('<21Q', bytes.fromhex(carrier['first_168_hex']))))
    _need(frame == actual, 'carrier named frame agrees with independent raw bytes')
    tid = binding['thread_id']
    _need(frame['sequence'] != 0 and frame['sequence'] % 2 == 0 and
          frame['owner_tid'] == tid and frame['active'] == 1 and
          frame['invocation_token'] != 0 and frame['nesting_depth'] != 0 and
          frame['core_clock_identity'] != 0 and
          frame['core_clock_identity'] == frame['natural_clock_identity'] and
          frame['core_thread_id'] == tid and frame['natural_thread_id'] == tid and
          0 < frame['natural_entry_sequence'] < frame['core_entry_sequence'] and
          frame['date_raw'] != 0 and 0 < frame['manager_identity'] <= (1 << 64) - 9 and
          frame['secondary_manager_identity'] == frame['manager_identity'] + 8 and
          frame['game_state_identity'] != 0 and frame['caller_return_rva'] == 0x2A9A8E2 and
          frame['natural_entry_rva'] == 0x2A9A570 and frame['entry_provenance_complete'] == 1 and
          frame['saved_mask02_admitted'] == 1 and frame['invocation_kind'] == 3,
          'actual thread/core/natural parent/date/context/RVA/mask/kind carrier provenance')
    _need((frame['nesting_depth'] == 1 and frame['parent_invocation_token'] == 0) or
          (frame['nesting_depth'] > 1 and frame['parent_invocation_token'] != 0 and
           frame['parent_invocation_token'] != frame['invocation_token']), 'carrier recursive token ancestry')
    _need(_int(hit.get('native_core_token'), 1) and
          hit['native_core_token'] == frame['invocation_token'] and
          hit.get('natural_parent_token') is None and hit.get('natural_attribution_ready') is False,
          'raw actual core token; natural event is not a scalar TLS token')
    return frame


# This standalone reader checks the literal CoreEvent serializer, not a NET
# projection. Optional business context remains raw and grants no game rule.
_CORE_SHAPES = {
    'Token': 'clock_identity=u64 sequence=u64 thread_id=u32?',
    'Roster': 'boundary=str capture_rva=u64 capture_event=Token begin_identity=u64? end_identity=u64? count=i32? complete=bool ordered_full_ids=u32[]',
    'Scope': 'observed=bool phase=str actual_entry_rva=u64 caller_return_rva=u64 primary_manager_identity=u64 secondary_manager_identity=u64 game_state_identity=u64 session_identity=u64? entry_event=Token date_raw=u64? prefix_date_raw=u64? absolute_day_raw=u32? entry_c0_raw=u8? saved_c0_raw=u8? saved_mask02_admitted=bool? saved_c0_observed_rva=u64 saved_c0_event=Token original_army_roster=Roster',
    'Occurrence': 'stored_index=i32 raw_full_id=i32? resolved_full_id=i32? physical_token=u64 used_fallback=bool? unavailable_reason=str',
    'Persistent': 'physical_token=u64 resolved_full_id=i32? unavailable_reason=str physical_values=raw',
    'Data': 'record_index=i32 persistent_regiment_id=i32? chunk_index=i32? persistent_physical_token=u64 state_raw=i32? native_record_admitted=bool unavailable_reason=str',
    'ArRg': 'occurrence=Occurrence resolved_magic_14_raw=u32? native_refresh_admitted=bool? native_loss_writer_skipped=bool? native_record_count=i32? records_complete=bool unavailable_reason=str records=Data[]',
    'Army': 'physical_token=u64 resolved_full_id=i32? native_arrg_occurrence_count=i32? unavailable_reason=str arrg_occurrences=ArRg[]',
    'Frame': 'native_persistent_occurrence_count=i32? native_army_refresh_occurrence_count=i32? capture_complete=bool persistent_occurrences=Occurrence[] army_refresh_occurrences=Occurrence[] persistent_objects=Persistent[] army_objects=Army[] missing_inputs=str[]',
    'SubjectIdentity': 'full_carmy_id=i32 resolved_full_carmy_id=i32? carmy_magic_14_raw=u32? public_unit_id=i32? unit_resolved_full_id=i32? unit_magic_14_raw=u32? unit_owner_character_id=i32? unit_full_carmy_id=i32?',
    'SubjectCoverage': 'schema_version=u32 mode=str scope_epoch=u64 bound_game_state_identity=u64 bound_owner_character_id=i32 requested_full_carmy_ids=i32[] manager_occurrences_complete=bool physical_closure_complete=bool subject_identity_witnesses=SubjectIdentity[] missing_inputs=str[]',
    'Event': 'journal_sequence=u64 manager_identity=u64 caller_return_rva=u64 raw_return_bits=u64 entry_date_raw=u64? returned_date_raw=u64? observed=bool original_called=bool original_returned=bool entry_provenance_complete=bool return_provenance_complete=bool parent_scope=Scope entry_event=Token returned_event=Token entry=Frame returned=Frame provenance_failures=str[] native_core_invocation_token=u64 parent_invocation_token=u64? core_invocation_nesting_depth=u64 core_carrier_published=bool core_carrier_source_epoch=u64',
}


def _core_typed(value: object, kind: str, depth: int = 0) -> None:
    _need(depth <= 24, 'bounded raw core record nesting')
    if kind.endswith('?'):
        if value is None: return
        return _core_typed(value, kind[:-1], depth + 1)
    if kind.endswith('[]'):
        _need(type(value) is list and len(value) <= 65536, 'bounded actual core array')
        for item in value: _core_typed(item, kind[:-2], depth + 1)
    elif kind in _CORE_SHAPES:
        fields = dict(field.split('=') for field in _CORE_SHAPES[kind].split())
        optional_subject = kind == 'Frame' and type(value) is dict and 'subject_coverage_v1' in value
        if optional_subject: fields['subject_coverage_v1'] = 'SubjectCoverage'
        _need(type(value) is dict and set(value) == set(fields), 'exact actual core ' + kind + ' serializer shape')
        for name, child in fields.items(): _core_typed(value[name], child, depth + 1)
    elif kind == 'raw':
        if value is None or type(value) in (bool, str): return
        if type(value) is int:
            _need(-(1 << 63) <= value < (1 << 64), 'raw core integer width'); return
        if type(value) is list:
            _need(len(value) <= 65536, 'bounded raw core list')
            for item in value: _core_typed(item, 'raw', depth + 1)
            return
        _need(type(value) is dict and len(value) <= 128 and all(type(k) is str for k in value), 'raw core JSON shape')
        for item in value.values(): _core_typed(item, 'raw', depth + 1)
    elif kind in ('str', 'bool'):
        _need(type(value) is (str if kind == 'str' else bool), 'actual core ' + kind + ' width')
    else:
        bits = int(kind[1:]); low = 0 if kind[0] == 'u' else -(1 << (bits - 1))
        high = (1 << bits) - 1 if kind[0] == 'u' else (1 << (bits - 1)) - 1
        _need(_int(value, low, high), 'actual core integer width ' + kind)


def _core_complete_frame(frame: dict, binding: Mapping[str, object], hit: dict) -> None:
    _need(frame['capture_complete'] is True and frame['missing_inputs'] == [], 'independent complete core frame required')
    maps = {}
    for prefix, objects in (('persistent', 'persistent_objects'), ('army_refresh', 'army_objects')):
        rows = frame[prefix + '_occurrences']; count = frame['native_' + prefix + '_occurrence_count']
        _need(type(count) is int and 0 <= count == len(rows) <= 65536 and
              [r['stored_index'] for r in rows] == list(range(count)), 'complete ordered core extent')
        copied = frame[objects]; tokens = [obj['physical_token'] for obj in copied]
        _need(all(tokens) and len(set(tokens)) == len(tokens), 'unique independently copied core objects')
        maps[objects] = dict(zip(tokens, copied))
        for row in rows:
            obj = maps[objects].get(row['physical_token'])
            _need(row['raw_full_id'] is not None and row['resolved_full_id'] is not None and
                  row['used_fallback'] is not None and row['unavailable_reason'] == '' and
                  obj is not None and obj['resolved_full_id'] == row['resolved_full_id'] and
                  obj['unavailable_reason'] == '' and
                  (row['used_fallback'] or row['raw_full_id'] == row['resolved_full_id']),
                  'complete core occurrence preserves full generation and physical identity')
    persistent = maps['persistent_objects'].get(_address(hit['regi_pointer']))
    _need(persistent is not None and persistent['resolved_full_id'] is not None and
          persistent['resolved_full_id'] & 0xFFFFFFFF == binding['regi_full_id_u32'],
          'selected full Regi physical object in actual core frame')
    for obj in frame['persistent_objects']:
        physical = obj['physical_values']
        _need(obj['resolved_full_id'] not in (None, -1) and obj['unavailable_reason'] == '' and
              type(physical) is dict and set(physical) == {'persistent_regiment_id', 'prepared_fraction_raw',
              'unavailable_reason', 'chunks'} and physical['persistent_regiment_id'] == obj['resolved_full_id'] and
              physical['unavailable_reason'] is None and type(physical['chunks']) is list and
              len(physical['chunks']) == 7, 'complete independently copied physical seven in core frame')
        _need(physical['prepared_fraction_raw'] is None or _int(physical['prepared_fraction_raw'], -(1 << 63), (1 << 63) - 1),
              'actual core prepared fraction width')
        if any(row['physical_token'] == obj['physical_token'] for row in frame['persistent_occurrences']):
            _need(physical['prepared_fraction_raw'] is not None, 'complete direct manager prepared fraction')
        for index, chunk in enumerate(physical['chunks']):
            raw = ('physical_index', 'current_soldiers', 'maximum_soldiers', 'owner_persistent_regiment_id',
                   'q_ordinal_raw', 'army_regiment_id_raw', 'exclusion_byte_14_raw', 'state_raw')
            context = ('owner_resolved_full_id', 'owner_guard_138_raw', 'origin_province_id',
                'origin_province_788_raw', 'origin_province_73c_raw', 'associated_arrg_resolved_full_id',
                'associated_army_raw_full_id', 'associated_army_resolved_full_id', 'army_byte_1d4_raw',
                'army_byte_1ec_raw', 'associated_unit_raw_full_id', 'associated_unit_resolved_full_id',
                'unit_170_raw', 'unit_position_owner_resolved_full_id', 'unit_position_holder_resolved_full_id')
            magic = ('owner_definition_magic_38_raw', 'associated_arrg_magic_raw', 'unit_position_province_magic_raw')
            predicates = ('native_army_in_combat', 'native_unit_position_eligible')
            fields = set(raw + context + magic + predicates) | {'context_unavailable_reason'}
            _need(type(chunk) is dict and set(chunk) in (fields, fields | {'refill_permission_switch_v1'}) and
                  all(_int(chunk[name], -(1 << 31), (1 << 31)-1) for name in raw) and
                  all(chunk[name] is None or _int(chunk[name], -(1 << 31), (1 << 31)-1) for name in context) and
                  all(chunk[name] is None or _int(chunk[name], 0, 0xFFFFFFFF) for name in magic) and
                  all(chunk[name] is None or type(chunk[name]) is bool for name in predicates) and
                  chunk['physical_index'] == index, 'complete ordered core physical slot raw fields')
            reason = chunk['context_unavailable_reason']
            _need(reason is None or (type(reason) is str and bool(reason)), 'raw optional core context reason')
            for name in ('exclusion_byte_14_raw', 'army_byte_1d4_raw', 'army_byte_1ec_raw'):
                _need(chunk[name] is None or 0 <= chunk[name] <= 255, 'copied core byte width')
            if 'refill_permission_switch_v1' in chunk:
                _need(type(chunk['refill_permission_switch_v1']) is dict, 'raw optional permission record')
    selected_armies = [obj for obj in frame['army_objects'] if obj['resolved_full_id'] == binding['army_full_id_i32']]
    _need(bool(selected_armies), 'selected full Army in actual core frame')
    selected_data = False
    data_tokens = []
    for army in frame['army_objects']:
        arrgs = army['arrg_occurrences']; count = army['native_arrg_occurrence_count']
        _need(army['resolved_full_id'] is not None and army['unavailable_reason'] == '' and
              type(count) is int and 0 <= count == len(arrgs) <= 65536 and
              [r['occurrence']['stored_index'] for r in arrgs] == list(range(count)), 'complete ordered core ArRg extent')
        for arrg in arrgs:
            occurrence = arrg['occurrence']; records = arrg['records']; count = arrg['native_record_count']
            _need(occurrence['raw_full_id'] is not None and occurrence['resolved_full_id'] is not None and
                  occurrence['physical_token'] != 0 and occurrence['used_fallback'] is not None and
                  (occurrence['used_fallback'] or occurrence['raw_full_id'] == occurrence['resolved_full_id']) and
                  occurrence['unavailable_reason'] == '' and
                  arrg['unavailable_reason'] == '' and arrg['records_complete'] is True and
                  arrg['native_refresh_admitted'] is not None, 'complete core ArRg branch copy')
            _need(arrg['resolved_magic_14_raw'] is not None and arrg['native_refresh_admitted'] ==
                  (arrg['resolved_magic_14_raw'] == 0x41725267 and occurrence['resolved_full_id'] != -1),
                  'actual core ArRg dispatch magic/full generation')
            _need([r['record_index'] for r in records] == list(range(len(records))), 'complete ordered core DATA')
            if arrg['native_refresh_admitted'] is True and arrg['native_loss_writer_skipped'] is False:
                _need(type(count) is int and 0 <= count == len(records) <= 65536 and
                      all(r['native_record_admitted'] for r in records), 'complete admitted core DATA extent')
            else:
                _need(records == [] and (arrg['native_refresh_admitted'] is False or
                      arrg['native_loss_writer_skipped'] is True), 'complete native non-DATA branch')
                if arrg['native_refresh_admitted'] is False:
                    _need(count is None and arrg['native_loss_writer_skipped'] is None,
                          'unadmitted core ArRg has no fabricated DATA branch')
            for record in records:
                token = record['persistent_physical_token']; data_tokens.append(token)
                obj = maps['persistent_objects'].get(token); slot = record['chunk_index']
                _need(record['persistent_regiment_id'] is not None and record['native_record_admitted'] is True and
                      record['unavailable_reason'] == '' and obj is not None and
                      obj['resolved_full_id'] == record['persistent_regiment_id'] and
                      _int(slot, 0, 6) and record['state_raw'] == obj['physical_values']['chunks'][slot]['state_raw'],
                      'complete actual DATA/physical chunk state association')
            if army in selected_armies and occurrence['resolved_full_id'] == binding['arrg_full_id_i32']:
                _need(occurrence['physical_token'] == _address(hit['arrg_pointer']), 'selected full ArRg physical identity')
                selected_data = selected_data or any(
                    r['persistent_regiment_id'] is not None and
                    r['persistent_regiment_id'] & 0xFFFFFFFF == binding['regi_full_id_u32'] and
                    r['persistent_physical_token'] == _address(hit['regi_pointer']) and
                    r['chunk_index'] == binding['physical_slot'] and r['native_record_admitted'] is True
                    for r in records)
    _need(selected_data, 'selected physical Regi/slot in actual core Army/ArRg DATA')
    for rows, objects, extra in ((frame['persistent_occurrences'], 'persistent_objects', data_tokens),
                                  (frame['army_refresh_occurrences'], 'army_objects', [])):
        ordered = []
        for token in [row['physical_token'] for row in rows] + extra:
            if token not in ordered: ordered.append(token)
        _need(list(maps[objects]) == ordered, 'complete core physical first-observation order and references')


def _join_actual_core(frame: dict, observation: object, binding: Mapping[str, object], hit: dict) -> dict:
    _need(type(observation) is dict, 'v4 requires one complete actual raw CoreEvent record')
    _core_typed(observation, 'Event')
    core = observation
    _need(all(core[key] is True for key in ('observed', 'original_called', 'original_returned',
          'entry_provenance_complete', 'return_provenance_complete', 'core_carrier_published')) and
          core['provenance_failures'] == [] and core['journal_sequence'] > 0 and
          core['core_carrier_source_epoch'] == _CARRIER_EPOCH, 'complete actual original core entry/return provenance')
    parent_token = core['parent_invocation_token']
    _need(core['native_core_invocation_token'] == frame['invocation_token'] and
          (0 if parent_token is None else parent_token) == frame['parent_invocation_token'] and
          core['core_invocation_nesting_depth'] == frame['nesting_depth'] and
          (parent_token is None or parent_token != 0), 'actual raw core invocation token/ancestry join')
    entry = {'clock_identity':frame['core_clock_identity'], 'sequence':frame['core_entry_sequence'],
             'thread_id':frame['core_thread_id']}
    natural = {'clock_identity':frame['natural_clock_identity'], 'sequence':frame['natural_entry_sequence'],
               'thread_id':frame['natural_thread_id']}
    scope = core['parent_scope']; returned = core['returned_event']; saved = scope['saved_c0_event']
    _need(core['entry_event'] == entry and scope['entry_event'] == natural and
          scope['observed'] is True and scope['phase'] == 'post_date' and
          scope['actual_entry_rva'] == frame['natural_entry_rva'] and
          scope['primary_manager_identity'] == core['manager_identity'] == frame['manager_identity'] and
          scope['secondary_manager_identity'] == frame['secondary_manager_identity'] and
          scope['game_state_identity'] == frame['game_state_identity'] and
          scope['date_raw'] == core['entry_date_raw'] == core['returned_date_raw'] == frame['date_raw'] and
          core['caller_return_rva'] == scope['saved_c0_observed_rva'] == frame['caller_return_rva'] and
          scope['saved_mask02_admitted'] is True and
          saved['clock_identity'] == returned['clock_identity'] == entry['clock_identity'] and
          saved['thread_id'] == returned['thread_id'] == entry['thread_id'] and
          entry['sequence'] < saved['sequence'] < returned['sequence'],
          'actual core entry/return and captured natural parent event/context/date join')
    _need(scope['saved_c0_raw'] is None or scope['saved_c0_raw'] & 0x02 != 0,
          'known saved C0 byte agrees with actual admitted mask02 branch')
    for label in ('entry', 'returned'): _core_complete_frame(core[label], binding, hit)
    return {'native_core_invocation_token':core['native_core_invocation_token'],
            'parent_invocation_token':parent_token, 'nesting_depth':core['core_invocation_nesting_depth'],
            'core_entry_event':dict(entry), 'core_returned_event':dict(returned),
            'natural_parent_event':dict(natural), 'source_epoch':_CARRIER_EPOCH,
            'entry_and_returned_complete':True, 'original_called_and_returned':True}


def _normalize_core_carrier_v4_12004(raw: bytes, binding: Mapping[str, object], core_observation: object) -> dict[str, object]:
    _need(isinstance(binding, Mapping) and binding.get('schema') in (_BINDING_V2_SCHEMA, _BINDING_V3_SCHEMA),
          'v4 exact owner binding v2 or explicit ordinary v3')
    native_campaign_null = binding['schema'] == _BINDING_V3_SCHEMA
    old_binding = dict(binding)
    if native_campaign_null:
        _need(old_binding.get('episode_projection') == 'native_campaign' and
              'episode_run_id' in old_binding and old_binding['episode_run_id'] is None,
              'v3 owner requires actual ordinary projection and null game episode')
        del old_binding['episode_projection']
    for key in ('carrier_module_path', 'carrier_source_epoch', 'source_dir'):
        _need(key in old_binding, 'owner carrier binding ' + key)
        del old_binding[key]
    old_binding['schema'] = BINDING_SCHEMA
    old_fields = {'schema', 'machine_id', 'exact_executable_sha256', 'pid', 'process_created_filetime',
                  'thread_id', 'regi_full_id_u32', 'physical_slot', 'arrg_full_id_i32', 'army_full_id_i32',
                  'connection_generation', 'episode_run_id', 'source_admission_receipt_sha256',
                  'observer_build_and_SYSTEM_gate_receipt_sha256'}
    _need(set(old_binding) == old_fields and _int(old_binding['thread_id'], 1, 0xFFFFFFFF),
          'exact owner binding v2 fields and actual thread')
    _need(type(binding['carrier_module_path']) is str and
          re.fullmatch(r'[A-Za-z]:[\\/].{1,4093}', binding['carrier_module_path']) is not None and
          '\x00' not in binding['carrier_module_path'] and
          PureWindowsPath(binding['carrier_module_path']).is_absolute() and
          PureWindowsPath(binding['carrier_module_path']).name.casefold() == 'xar_ck3_bridge.dll' and
          _int(binding['carrier_source_epoch'], _CARRIER_EPOCH, _CARRIER_EPOCH), 'actual owner carrier module path/source epoch')
    source_dir = binding['source_dir']
    _need(type(source_dir) is str and 0 < len(source_dir) <= 4096 and '\x00' not in source_dir and
          PureWindowsPath(source_dir).is_absolute() and PureWindowsPath(source_dir).name == 'refill_add_live_12004',
          'owner actual fixed-basename source directory; existence is preparation admission authority')
    rows = [json.loads(line, object_pairs_hook=_unique_json_object) for line in raw.decode('utf-8').splitlines()]
    _need(len(rows) == 6 and all(type(row) is dict for row in rows), 'v4 six native rows')
    start, a, b, pair, _budget, _terminal = rows
    _need(start.get('schema') == _V4_SCHEMA, 'exact v4 native source')
    extras = ('carrier_module_path', 'carrier_module_base', 'carrier_export_rva',
              'carrier_address', 'carrier_source_epoch', 'carrier_header_64_hex')
    _need(all(key in start for key in extras), 'complete actual carrier start metadata')
    _need(start['carrier_module_path'] == binding['carrier_module_path'] and
          type(start['carrier_source_epoch']) is int and start['carrier_source_epoch'] == _CARRIER_EPOCH and
          start['carrier_header_64_hex'] == _CARRIER_HEADER_HEX, 'actual carrier source/header binding')
    module = _address(start['carrier_module_base']); rva = _address(start['carrier_export_rva'])
    _need(module <= (1 << 64) - 1 - rva and _address(start['carrier_address']) == module + rva,
          'actual exported carrier address')
    frames = [_carrier_frame(hit, start, binding) for hit in (a, b)]
    carrier_evidence = a['core_carrier_v1']
    _need(frames[0] == frames[1] and a['core_carrier_v1'] == b['core_carrier_v1'],
          'same entire stable carrier frame and fence across actual pre/post ADD')
    _need(pair.get('carrier_pair_same_token') is True and _int(pair.get('native_core_token'), 1) and
          pair['native_core_token'] == frames[0]['invocation_token'], 'actual pair same core invocation token')
    join = _join_actual_core(frames[0], core_observation, binding, a)
    # Projection reuses all exact v3/v2 physical/stack/cleanup checks. Only the
    # newly validated fields are removed; unknown aliases still fail there.
    start['schema'] = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
    for key in extras: del start[key]
    for hit in (a, b):
        del hit['core_carrier_v1']; hit['native_core_token'] = None
    del pair['carrier_pair_same_token']; del pair['native_core_token']
    projection = ('\n'.join(json.dumps(row, separators=(',', ':')) for row in rows) + '\n').encode()
    item = _normalize_stack_q_source_v3_12004(
        projection, old_binding, _native_campaign_null=native_campaign_null)
    item.update(raw_sha256=hashlib.sha256(raw).hexdigest(), raw_schema=_V4_SCHEMA,
                owner_binding=dict(binding), native_core_token=frames[0]['invocation_token'],
                native_event_date_raw=frames[0]['date_raw'], same_core_invocation_join_ready=True,
                natural_attribution_ready=True, core_invocation_join_v1=join,
                core_carrier_v1=carrier_evidence)
    # The preserved evidence identifies one instruction in one actual core.
    # It cannot assign the whole frame NET, toggle effect or complete window.
    return item


def normalize_instruction_local_refill_add_12004(raw: bytes, binding: Mapping[str, object], *,
                                                core_observation: object = None) -> dict[str, object]:
    """Accept exact native v2/v3/v4; v4 requires an independent raw core join."""
    _need(type(raw) is bytes and 0 < len(raw) <= 131072, 'bounded immutable native NDJSON')
    first = raw.decode('utf-8').splitlines()
    _need(bool(first), 'native start row')
    start = json.loads(first[0])
    _need(type(start) is dict, 'native start object')
    if start.get('schema') == _V4_SCHEMA:
        return _normalize_core_carrier_v4_12004(raw, binding, core_observation)
    if start.get('schema') == 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3':
        return _normalize_stack_q_source_v3_12004(raw, binding)
    return _normalize_instruction_local_refill_add_v2_12004(raw, binding)


def attach_instruction_local_refill_add_12004(net_qualification: Mapping[str, object], raw: bytes,
                                             binding: Mapping[str, object], *,
                                             core_observation: object = None) -> dict[str, object]:
    """Publish independent instruction evidence without changing the NET contract."""
    _need(net_qualification.get('actual_ADD_observed') is False, 'existing NET source remains unchanged')
    item = normalize_instruction_local_refill_add_12004(raw,binding,core_observation=core_observation)
    return {**net_qualification,'instruction_local_ADD_v1':item,'instruction_and_NET_parent_join_ready':False}
