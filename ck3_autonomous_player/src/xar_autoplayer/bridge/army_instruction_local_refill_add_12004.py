"""Strict native hardware ADD wire consumer; no process access or evaluation.

The caller owns the fresh process/cohort/build/SYSTEM admission whose pins are
retained in binding. Matching those identifiers does not prove a native parent,
date, complete window, toggle effect, or the source of a prior core NET record.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
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


def normalize_instruction_local_refill_add_12004(raw: bytes, binding: Mapping[str, object]) -> dict[str, object]:
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


def attach_instruction_local_refill_add_12004(net_qualification: Mapping[str, object], raw: bytes,
                                             binding: Mapping[str, object]) -> dict[str, object]:
    """Publish independent instruction evidence without changing the NET contract."""
    _need(net_qualification.get('actual_ADD_observed') is False, 'existing NET source remains unchanged')
    item = normalize_instruction_local_refill_add_12004(raw,binding)
    return {**net_qualification,'instruction_local_ADD_v1':item,'instruction_and_NET_parent_join_ready':False}
