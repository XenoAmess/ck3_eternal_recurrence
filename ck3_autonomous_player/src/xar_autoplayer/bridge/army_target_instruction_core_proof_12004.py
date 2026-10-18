"""Explicit target proof from original native response bytes; no process access.

This separate contract never weakens the legacy complete-manager consumer. A
small view alone is not evidence: consumption re-extracts it from the original
response-line bytes and verifies that response's range/hash/request/query. File
identity and admission authority remain the caller's responsibility.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import re


_spec = importlib.util.spec_from_file_location(
    '_xar_target_instruction_shared_12004',
    Path(__file__).with_name('army_instruction_local_refill_add_12004.py'))
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)
_need, _int, _address = _shared._need, _shared._int, _shared._address

PROOF_SCHEMA = 'xar.ck3.explicit_target_instruction_core_proof.v1'
BINDING_SCHEMA = 'xar.ck3.refill_ADD_12004.owner_binding.v4'
RAW_SCHEMA = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v5'
ITEM_SCHEMA = 'xar.ck3.refill_ADD_12004.target_instruction_item.v1'
FAMILY = 'actual_army_regular_core_observations_v1'
MAX_PARENT_BYTES = 32 * 1024 * 1024
MAX_PROOF_BYTES = 64 * 1024
MAX_PARENT_PROOF_BYTES = 16 * 1024


def _encoded(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True,
                      allow_nan=False).encode('utf-8')


def _sha(value: object) -> bool:
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _owner(binding: Mapping) -> dict:
    fields = {'schema', 'machine_id', 'exact_executable_sha256', 'pid',
              'process_created_filetime', 'thread_id', 'regi_full_id_u32',
              'physical_slot', 'arrg_full_id_i32', 'army_full_id_i32',
              'connection_generation', 'episode_run_id', 'episode_projection',
              'source_admission_receipt_sha256',
              'observer_build_and_SYSTEM_gate_receipt_sha256', 'carrier_module_path',
              'carrier_source_epoch', 'source_dir', 'admission_mailbox_thread_id',
              'thread_policy', 'maximum_owned_threads'}
    _need(isinstance(binding, Mapping) and set(binding) == fields and
          binding['schema'] == BINDING_SCHEMA, 'exact explicit worker owner binding v4')
    _need(binding['thread_id'] is None and binding['thread_policy'] == 'carrier_owned_target' and
          _int(binding['maximum_owned_threads'], 1, 256) and
          _int(binding['admission_mailbox_thread_id'], 1, 0xFFFFFFFF),
          'unselected worker; admission mailbox is not a callback worker')
    episode = binding['episode_run_id']; projection = binding['episode_projection']
    _need(projection is None or (type(projection) is str and 0 < len(projection) <= 256),
          'preserved raw episode projection')
    _need((episode is None and projection == 'native_campaign') or
          (type(episode) is str and 0 < len(episode) <= 256 and episode != 'None'),
          'actual ordinary null or original nonempty game episode')
    _need(type(binding['carrier_module_path']) is str and
          len(binding['carrier_module_path']) <= 4096 and
          PureWindowsPath(binding['carrier_module_path']).is_absolute() and
          PureWindowsPath(binding['carrier_module_path']).name.casefold() == 'xar_ck3_bridge.dll' and
          '\x00' not in binding['carrier_module_path'] and
          _int(binding['carrier_source_epoch'], _shared._CARRIER_EPOCH, _shared._CARRIER_EPOCH),
          'owner exact carrier path and epoch')
    _need(type(binding['source_dir']) is str and
          PureWindowsPath(binding['source_dir']).is_absolute() and
          PureWindowsPath(binding['source_dir']).name == 'refill_add_live_12004' and
          len(binding['source_dir']) <= 4096 and '\x00' not in binding['source_dir'],
          'owner actual fixed-basename source directory')
    old = {k:v for k,v in binding.items() if k not in {
        'episode_projection', 'carrier_module_path', 'carrier_source_epoch', 'source_dir',
        'admission_mailbox_thread_id', 'thread_policy', 'maximum_owned_threads'}}
    old['schema'] = _shared.BINDING_SCHEMA
    return old


def _worker_wire(raw: bytes, binding: Mapping) -> tuple[dict, dict, dict, dict, dict]:
    """Validate event-owned generations; reuse original raw physical/stack guards."""
    old = _owner(binding)
    _need(type(raw) is bytes and 0 < len(raw) <= 131072, 'bounded immutable v5 native wire')
    rows = [json.loads(line, object_pairs_hook=_shared._unique_json_object)
            for line in raw.decode('utf-8').splitlines()]
    _need(all(type(r) is dict for r in rows) and
          6 <= len(rows) <= 2 * binding['maximum_owned_threads'] + 6 and
          rows[0].get('kind') == 'start' and rows[-1].get('kind') == 'terminal', 'bounded v5 event rows')
    main = [r for r in rows if r.get('kind') not in ('thread_armed', 'thread_retired')]
    _need(len(main) == 6 and [r.get('kind') for r in main] == [
        'start', 'raw_ADD_boundary', 'raw_ADD_boundary', 'physical_ADD_pair',
        'debug_hit_budget', 'terminal'], 'one original worker pair and terminal')
    start, pre, post, pair, budget, terminal = main
    extras = {'thread_policy', 'maximum_owned_threads', 'armed_thread_ids', 'armed_thread_count'}
    _need(start.get('schema') == RAW_SCHEMA and start.get('thread_id') is None and
          start.get('thread_policy') == binding['thread_policy'] and
          type(start.get('maximum_owned_threads')) is int and
          start['maximum_owned_threads'] == binding['maximum_owned_threads'] and
          start.get('armed_thread_ids') == [] and _int(start.get('armed_thread_count'), 0, 0),
          'v5 starts before event-owned arming; no fabricated callback thread')
    _need(all(k in start for k in extras), 'complete v5 worker start metadata')
    selected_tid, selected_generation = pre.get('thread_id'), pre.get('thread_generation')
    _need(_int(selected_tid, 1, 0xFFFFFFFF) and _int(selected_generation, 1) and
          post.get('thread_id') == selected_tid and type(post.get('thread_id')) is int and
          post.get('thread_generation') == selected_generation and
          type(post.get('thread_generation')) is int,
          'same actual stopped worker generation at both boundaries')
    active = {}; seen = set(); peak = 0; prior_ordinal = 0; pair_published = False
    for row in rows:
        kind = row.get('kind')
        if kind == 'physical_ADD_pair': pair_published = True
        _need(not (pair_published and kind in ('thread_armed', 'thread_retired', 'raw_ADD_boundary')),
              'thread lifecycle and stopped boundaries precede the published pair')
        if kind in ('thread_armed', 'thread_retired', 'raw_ADD_boundary'):
            ordinal = row.get('all_debug_event_ordinal')
            _need(_int(ordinal, prior_ordinal + 1), 'strict all-debug-event source order')
            prior_ordinal = ordinal
        if kind == 'thread_armed':
            _need(set(row) == {'kind', 'thread_id', 'thread_generation', 'all_debug_event_ordinal',
                'source', 'owned_handle_verified', 'debug_registers_armed'} and
                _int(row['thread_id'], 1, 0xFFFFFFFF) and _int(row['thread_generation'], 1) and
                row['source'] in ('CREATE_PROCESS_DEBUG_EVENT', 'CREATE_THREAD_DEBUG_EVENT') and
                row['owned_handle_verified'] is True and row['debug_registers_armed'] is True,
                'exact successfully armed event-owned thread generation')
            identity = (row['thread_id'], row['thread_generation'])
            _need(row['thread_id'] not in active and identity not in seen, 'no reused live or retired owned generation')
            active[row['thread_id']] = row['thread_generation']; seen.add(identity)
            peak = max(peak, len(active))
            _need(len(seen) <= binding['maximum_owned_threads'], 'finite total owned thread generations including retired')
        elif kind == 'thread_retired':
            _need(set(row) == {'kind', 'thread_id', 'thread_generation', 'all_debug_event_ordinal',
                'had_saved_debug', 'owned_handle_closed', 'saved_debug_retired'} and
                _int(row['thread_id'], 1, 0xFFFFFFFF) and _int(row['thread_generation'], 1) and
                active.get(row['thread_id']) == row['thread_generation'] and
                row['had_saved_debug'] is True and row['owned_handle_closed'] is True and
                row['saved_debug_retired'] is True, 'exact exited generation retirement and saved DR disposal')
            del active[row['thread_id']]
        elif kind == 'raw_ADD_boundary':
            _need(active.get(selected_tid) == selected_generation,
                  'selected stopped worker generation is independently armed and still owned')
    _need(post['all_debug_event_ordinal'] == pre['all_debug_event_ordinal'] + 1,
          'adjacent entire-debug-event boundaries')
    for record in (pair, terminal):
        _need(type(record.get('selected_thread_id')) is int and record['selected_thread_id'] == selected_tid and
              type(record.get('selected_thread_generation')) is int and
              record['selected_thread_generation'] == selected_generation, 'actual selected worker pair/terminal identity')
    _need(terminal.get('thread_policy') == binding['thread_policy'] and
          type(terminal.get('maximum_owned_threads')) is int and
          terminal['maximum_owned_threads'] == binding['maximum_owned_threads'] and
          _int(terminal.get('peak_owned_thread_count'), peak, peak), 'actual bounded owned-thread peak')
    old['thread_id'] = selected_tid
    carrier_extras = ('carrier_module_path', 'carrier_module_base', 'carrier_export_rva',
        'carrier_address', 'carrier_source_epoch', 'carrier_header_64_hex')
    _need(all(k in start for k in carrier_extras) and
          start['carrier_module_path'] == binding['carrier_module_path'] and
          _int(start['carrier_source_epoch'], _shared._CARRIER_EPOCH, _shared._CARRIER_EPOCH) and
          start['carrier_header_64_hex'] == _shared._CARRIER_HEADER_HEX, 'complete actual carrier start metadata')
    module, rva = _address(start['carrier_module_base']), _address(start['carrier_export_rva'])
    _need(module <= (1 << 64) - 1 - rva and _address(start['carrier_address']) == module + rva,
          'actual exported carrier address')
    actual_binding = {**binding, 'thread_id':selected_tid}
    frames = [_shared._carrier_frame(hit, start, actual_binding) for hit in (pre, post)]
    _need(frames[0] == frames[1] and pre['core_carrier_v1'] == post['core_carrier_v1'] and
          pair.get('carrier_pair_same_token') is True and
          _int(pair.get('native_core_token'), 1) and pair['native_core_token'] == frames[0]['invocation_token'],
          'same stable entire carrier and invocation token across one worker pair')
    projected = copy.deepcopy(main)
    projected[0]['schema'] = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
    projected[0]['thread_id'] = selected_tid
    for k in extras | set(carrier_extras): del projected[0][k]
    for hit in projected[1:3]:
        for k in ('core_carrier_v1', 'thread_generation', 'all_debug_event_ordinal'): del hit[k]
        hit['native_core_token'] = None
    for k in ('carrier_pair_same_token', 'native_core_token', 'selected_thread_id', 'selected_thread_generation'):
        del projected[3][k]
    for k in ('thread_policy', 'maximum_owned_threads', 'peak_owned_thread_count',
              'selected_thread_id', 'selected_thread_generation'): del projected[5][k]
    # Only named new fields were removed. Unknown aliases still reach the exact
    # original v3/v2 field checks. Original 252B/28B hex strings are untouched.
    physical = _shared._normalize_stack_q_source_v3_12004(
        b'\n'.join(_encoded(r) for r in projected) + b'\n', old,
        _native_campaign_null=binding['episode_run_id'] is None)
    physical.update(raw_sha256=hashlib.sha256(raw).hexdigest(), raw_schema=RAW_SCHEMA,
        owner_binding=dict(binding), selected_thread_id=selected_tid,
        selected_thread_generation=selected_generation)
    return physical, frames[0], pre, post, start


def _parent(parent_response: bytes, parent_proof: Mapping, binding: Mapping,
            path: tuple | None, *, native_core_token: int) -> tuple[dict, dict, dict, tuple]:
    _need(type(parent_response) is bytes and 0 < len(parent_response) <= MAX_PARENT_BYTES and
          parent_response.endswith(b'\n') and parent_response.count(b'\n') == 1,
          'one bounded complete original native response JSONL line including newline')
    _need(isinstance(parent_proof, Mapping) and len(_encoded(parent_proof)) <= MAX_PARENT_PROOF_BYTES,
          'bounded actual parent range proof')
    fields = ('path', 'file_identity', 'response_line', 'native_request_id', 'query_sequence')
    _need(all(k in parent_proof for k in fields), 'actual original parent source pins')
    pin = {k:copy.deepcopy(parent_proof[k]) for k in fields}
    line = pin['response_line']
    _need(type(pin['path']) is str and 0 < len(pin['path']) <= 4096 and
          PureWindowsPath(pin['path']).is_absolute() and '\x00' not in pin['path'] and
          type(pin['file_identity']) is list and len(pin['file_identity']) == 2 and
          all(_int(n) for n in pin['file_identity']), 'original file identity and path; I/O verification is caller authority')
    _need(type(line) is dict and set(line) == {'begin', 'end', 'sha256'} and
          _int(line['begin']) and _int(line['end'], line['begin'] + 1) and
          line['end'] - line['begin'] == len(parent_response) and _sha(line['sha256']) and
          hashlib.sha256(parent_response).hexdigest() == line['sha256'], 'original full response-line range SHA/length')
    _need(type(pin['native_request_id']) is str and 0 < len(pin['native_request_id']) <= 256 and
          _int(pin['query_sequence'], 1), 'actual request/query identity')
    envelope = json.loads(parent_response, object_pairs_hook=_shared._unique_json_object)
    _need(type(envelope) is dict and envelope.get('direction') == 'dll-to-python', 'original native response direction')
    msg = envelope.get('message'); _need(type(msg) is dict, 'original native protocol message')
    _need(msg.get('type') == 'command_result' and msg.get('protocol_version') == 1 and
          type(msg.get('protocol_version')) is int and msg.get('ok') is True and
          msg.get('request_id') == pin['native_request_id'], 'original successful protocol request identity')
    result = msg.get('result'); _need(type(result) is dict, 'original query result')
    _need(result.get('step') == 'query-army-strengths-v1' and result.get('accepted') is True and
          result.get('status') in ('available', 'partial') and
          type(result.get('query_sequence')) is int and result['query_sequence'] == pin['query_sequence'] and
          result.get('army_strengths_profile') == 'observed_history_full_v1', 'original full-history query sequence/profile')
    rows = result.get('army_strengths')
    _need(type(rows) is list and 0 < len(rows) <= 65536 and all(type(r) is dict for r in rows), 'native Army rows')
    selected = [i for i,r in enumerate(rows) if type(r.get('native_carmy_id')) is int and
                r['native_carmy_id'] == binding['army_full_id_i32']]
    _need(len(selected) == 1, 'unique original full CArmy subject row including zero')
    if path is None:
        family = rows[selected[0]].get(FAMILY)
        _need(type(family) is dict and type(family.get('events')) is list and
              len(family['events']) <= 65536, 'bounded original Core events for automatic token lookup')
        events = [i for i,e in enumerate(family['events']) if type(e) is dict and
                  e.get('native_core_invocation_token') == native_core_token]
        _need(len(events) == 1, 'unique original same-token Core event for automatic lookup')
        path = ('message', 'result', 'army_strengths', selected[0], FAMILY, 'events', events[0])
    _need(type(path) is tuple and len(path) == 7 and path[:3] == ('message', 'result', 'army_strengths') and
          _int(path[3], 0, 65535) and path[4:6] == (FAMILY, 'events') and _int(path[6], 0, 65535) and
          selected == [path[3]], 'literal native same-subject Core event path; no arbitrary dictionary substitute')
    family = rows[path[3]].get(FAMILY)
    _need(type(family) is dict and set(family) == {'schema_version', 'source', 'membership_basis',
        'observer_initialized', 'observer_installed', 'latest_journal_sequence', 'overwritten_events',
        'publication_failures', 'events'} and _int(family['schema_version'], 1, 1) and
        family['source'] == 'native_natural_army_regular_core_entry_return' and
        type(family['membership_basis']) is str and bool(family['membership_basis']) and
        family['observer_initialized'] is True and family['observer_installed'] is True and
        _int(family['overwritten_events']) and _int(family['publication_failures']) and
        _int(family['latest_journal_sequence'], 1) and type(family['events']) is list and
        path[6] < len(family['events']) <= 65536, 'actual installed bounded Core journal family')
    core = family['events'][path[6]]
    _need(type(core) is dict and _int(core.get('native_core_invocation_token'), 1) and
          sum(type(e) is dict and e.get('native_core_invocation_token') == core['native_core_invocation_token']
              for e in family['events']) == 1 and
          _int(core.get('journal_sequence'), 1, family['latest_journal_sequence']), 'unique complete original Core token')
    _need(core['native_core_invocation_token'] == native_core_token, 'original Core event is the actual instruction token')
    return core, pin, {k:copy.deepcopy(v) for k,v in family.items() if k != 'events'}, path


def _occurrence(row: dict, *, exact_id: int | None = None, token: int | None = None) -> None:
    _shared._core_typed(row, 'Occurrence')
    _need(row['raw_full_id'] is not None and row['resolved_full_id'] is not None and
          row['used_fallback'] is not None and row['physical_token'] != 0 and
          row['unavailable_reason'] == '' and
          (row['used_fallback'] or row['raw_full_id'] == row['resolved_full_id']), 'complete original occurrence identity')
    if exact_id is not None:
        _need(row['raw_full_id'] == row['resolved_full_id'] == exact_id and row['used_fallback'] is False,
              'selected exact full generation without fallback')
    if token is not None: _need(row['physical_token'] == token, 'selected exact physical identity')


def _physical_seven(obj: dict, regi: int) -> None:
    _shared._core_typed(obj, 'Persistent')
    p = obj['physical_values']
    _need(obj['resolved_full_id'] == regi and obj['unavailable_reason'] == '' and
          type(p) is dict and set(p) == {'persistent_regiment_id', 'prepared_fraction_raw',
          'unavailable_reason', 'chunks'} and p['persistent_regiment_id'] == regi and
          (p['prepared_fraction_raw'] is None or _int(p['prepared_fraction_raw'], -(1 << 63), (1 << 63)-1)) and
          p['unavailable_reason'] is None and type(p['chunks']) is list and len(p['chunks']) == 7,
          'complete copied numeric target Regi seven; no manufactured raw bytes')
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
    for i,c in enumerate(p['chunks']):
        _need(type(c) is dict and set(c) in (fields, fields | {'refill_permission_switch_v1'}) and
              all(_int(c[k], -(1 << 31), (1 << 31)-1) for k in raw) and
              all(c[k] is None or _int(c[k], -(1 << 31), (1 << 31)-1) for k in context) and
              all(c[k] is None or _int(c[k], 0, 0xFFFFFFFF) for k in magic) and
              all(c[k] is None or type(c[k]) is bool for k in predicates) and c['physical_index'] == i and
              all(c[k] is None or 0 <= c[k] <= 255 for k in
                  ('exclusion_byte_14_raw', 'army_byte_1d4_raw', 'army_byte_1ec_raw')) and
              (c['context_unavailable_reason'] is None or
               (type(c['context_unavailable_reason']) is str and bool(c['context_unavailable_reason']))) and
              ('refill_permission_switch_v1' not in c or type(c['refill_permission_switch_v1']) is dict),
              'complete ordered copied target numeric physical slot')


def _target_frame(frame: dict, binding: Mapping, hit: dict, carrier: dict) -> dict:
    _shared._core_typed(frame, 'Frame')
    coverage = frame.get('subject_coverage_v1')
    _need(type(coverage) is dict and _int(coverage['schema_version'], 1, 1) and
          coverage['mode'] == 'explicit_full_carmy_physical_closure' and
          _int(coverage['scope_epoch'], 1) and
          coverage['bound_game_state_identity'] == carrier['game_state_identity'] and
          coverage['manager_occurrences_complete'] is True and
          coverage['bound_owner_character_id'] != -1 and
          coverage['requested_full_carmy_ids'].count(binding['army_full_id_i32']) == 1,
          'actual explicitly scoped manager identity witness; no global completeness claim')
    witnesses = [w for w in coverage['subject_identity_witnesses'] if
                 w['full_carmy_id'] == binding['army_full_id_i32']]
    _need(len(witnesses) == 1, 'unique independently copied CArmy/Unit/owner witness')
    w = witnesses[0]
    _need(w['resolved_full_carmy_id'] == w['full_carmy_id'] and w['carmy_magic_14_raw'] == 0x41726D79 and
          w['public_unit_id'] not in (None, -1) and w['unit_resolved_full_id'] == w['public_unit_id'] and
          w['unit_magic_14_raw'] == 0x556E6974 and
          w['unit_owner_character_id'] == coverage['bound_owner_character_id'] and
          w['unit_full_carmy_id'] == w['full_carmy_id'], 'exact full CArmy/Unit generation/magic/owner binding')
    for prefix in ('persistent', 'army_refresh'):
        rows = frame[prefix + '_occurrences']; count = frame['native_' + prefix + '_occurrence_count']
        _need(_int(count, 0, 65536) and len(rows) == count and
              [r['stored_index'] for r in rows] == list(range(count)), 'complete original manager occurrence extent')
        for row in rows: _occurrence(row)
    armies = [a for a in frame['army_objects'] if a['resolved_full_id'] == binding['army_full_id_i32']]
    _need(len(armies) == 1 and armies[0]['physical_token'] != 0 and armies[0]['unavailable_reason'] == '',
          'unique copied target Army physical generation')
    army = armies[0]
    manager_aliases = [r for r in frame['army_refresh_occurrences'] if r['resolved_full_id'] == binding['army_full_id_i32']]
    _need(bool(manager_aliases), 'target Army occurs in the actual original manager roster')
    for row in manager_aliases:
        _occurrence(row, exact_id=binding['army_full_id_i32'], token=army['physical_token'])
    arrgs = army['arrg_occurrences']
    _need(_int(army['native_arrg_occurrence_count'], 1, 65536) and
          len(arrgs) == army['native_arrg_occurrence_count'] and
          [a['occurrence']['stored_index'] for a in arrgs] == list(range(len(arrgs))),
          'entire target Army ArRg order and aliases')
    target_arrgs = []; aliases = []; branches = []
    regi = _shared._i32(binding['regi_full_id_u32']); pointer = _address(hit['regi_pointer'])
    for arrg in arrgs:
        occurrence = arrg['occurrence']; _occurrence(occurrence)
        _need(arrg['unavailable_reason'] == '' and arrg['records_complete'] is True and
              arrg['resolved_magic_14_raw'] is not None and arrg['native_refresh_admitted'] ==
              (arrg['resolved_magic_14_raw'] == 0x41725267 and occurrence['resolved_full_id'] != -1),
              'actual complete target Army ArRg dispatch branches')
        records = arrg['records']
        _need([r['record_index'] for r in records] == list(range(len(records))), 'complete original DATA order')
        if arrg['native_refresh_admitted'] is True and arrg['native_loss_writer_skipped'] is False:
            _need(_int(arrg['native_record_count'], 0, 65536) and len(records) == arrg['native_record_count'] and
                  all(r['native_record_admitted'] is True and r['unavailable_reason'] == '' and
                      r['persistent_regiment_id'] is not None and r['persistent_physical_token'] != 0 and
                      _int(r['chunk_index'], 0, 6) and r['state_raw'] is not None for r in records),
                  'entire native admitted DATA for alias enumeration')
        else:
            _need(records == [] and ((arrg['native_refresh_admitted'] is False and
                  arrg['native_loss_writer_skipped'] is None and arrg['native_record_count'] is None) or
                  (arrg['native_refresh_admitted'] is True and arrg['native_loss_writer_skipped'] is True)),
                  'known original non-DATA branch; no invented physical closure')
        for record in records:
            if record['persistent_regiment_id'] == regi or record['persistent_physical_token'] == pointer:
                _need(record['persistent_regiment_id'] == regi and record['persistent_physical_token'] == pointer,
                      'all target full-ID/physical aliases agree')
                aliases.append({'arrg_occurrence':copy.deepcopy(occurrence), 'record':copy.deepcopy(record)})
        branches.append({k:copy.deepcopy(v) for k,v in arrg.items() if k != 'records'})
        if occurrence['resolved_full_id'] == binding['arrg_full_id_i32']:
            _occurrence(occurrence, exact_id=binding['arrg_full_id_i32'], token=_address(hit['arrg_pointer']))
            _need(arrg['native_refresh_admitted'] is True and arrg['native_loss_writer_skipped'] is False,
                  'selected ArRg took the actual non-override DATA branch')
            target_arrgs.append(arrg)
    _need(bool(target_arrgs) and all(a['records'] == target_arrgs[0]['records'] for a in target_arrgs),
          'all selected ArRg aliases have the same complete DATA')
    records = target_arrgs[0]['records']
    _need(len(records) == hit['data_count'] and all(
          r['record_index'] == d['stored_index'] and r['persistent_regiment_id'] is not None and
          r['persistent_regiment_id'] & 0xFFFFFFFF == d['persistent_full_id_u32'] and
          r['chunk_index'] == d['physical_ordinal_u32'] for r,d in zip(records, hit['DATA'])),
          'entire selected Core DATA agrees with independent instruction DATA copy')
    objects = [p for p in frame['persistent_objects'] if p['physical_token'] == pointer or p['resolved_full_id'] == regi]
    _need(len(objects) == 1 and objects[0]['physical_token'] == pointer, 'unique target Regi physical generation')
    obj = objects[0]; _physical_seven(obj, regi)
    _need(bool(aliases) and any(a['record']['chunk_index'] == binding['physical_slot'] and
          a['arrg_occurrence']['resolved_full_id'] == binding['arrg_full_id_i32'] for a in aliases),
          'selected physical Regi/slot in actual target DATA aliases')
    for alias in aliases:
        r = alias['record']
        _need(r['state_raw'] == obj['physical_values']['chunks'][r['chunk_index']]['state_raw'],
              'every target DATA alias agrees with independently copied physical slot state')
    selected = obj['physical_values']['chunks'][binding['physical_slot']]
    _need(selected['owner_persistent_regiment_id'] == regi and
          selected['army_regiment_id_raw'] == binding['arrg_full_id_i32'] and
          selected['q_ordinal_raw'] == hit['q_index'], 'copied selected slot owner/ArRg/q-index domain')
    return {'global_capture_complete_as_observed':frame['capture_complete'],
        'global_missing_inputs_as_observed':copy.deepcopy(frame['missing_inputs']),
        'subject_coverage_v1':copy.deepcopy(coverage), 'target_army_manager_aliases':copy.deepcopy(manager_aliases),
        'target_army_physical_token':army['physical_token'],
        'target_army_native_arrg_count':army['native_arrg_occurrence_count'],
        'entire_target_army_arrg_branch_roster':branches,
        'selected_arrg_complete_DATA':copy.deepcopy(target_arrgs[0]),
        'all_target_Regi_DATA_aliases':aliases, 'target_Regi_numeric_seven':copy.deepcopy(obj),
        'target_DATA_alias_enumeration_complete':True,
        'numeric_seven_capture_time':'original Core entry-or-return boundary, distinct from instruction traps'}


def build_target_instruction_core_proof_12004(*, parent_response: bytes, parent_proof: Mapping,
        binding: Mapping, raw: bytes, core_event_path: tuple | None = None) -> dict:
    """Extract only after validating original full parent bytes in this call."""
    physical, carrier, pre, post, _start = _worker_wire(raw, binding)
    core, pin, family, core_event_path = _parent(parent_response, parent_proof, binding, core_event_path,
        native_core_token=carrier['invocation_token'])
    join = _shared._join_actual_core_provenance(carrier, core)
    entry = _target_frame(core['entry'], binding, pre, carrier)
    returned = _target_frame(core['returned'], binding, post, carrier)
    _need(entry['subject_coverage_v1']['scope_epoch'] == returned['subject_coverage_v1']['scope_epoch'] and
          entry['subject_coverage_v1']['bound_owner_character_id'] == returned['subject_coverage_v1']['bound_owner_character_id'] and
          entry['subject_coverage_v1']['subject_identity_witnesses'] == returned['subject_coverage_v1']['subject_identity_witnesses'] and
          entry['target_army_physical_token'] == returned['target_army_physical_token'],
          'independent entry/return target CArmy/Unit/owner generation and scope remain bound')
    proof = {'schema':PROOF_SCHEMA, 'source_kind':'original_native_response_target_copy',
        'owner_binding':dict(binding), 'full_parent':pin, 'core_event_path':list(core_event_path),
        'full_parent_hash_domain':'entire original native response JSONL line including newline',
        'source_family':family, 'core_provenance':{k:copy.deepcopy(v) for k,v in core.items() if k not in ('entry','returned')},
        'core_invocation_join':join, 'entry_target':entry, 'returned_target':returned,
        'instruction_raw_sha256':physical['raw_sha256'],
        'instruction_trap_bytes':{'before_physical_seven_hex':pre['physical_seven_hex'],
            'after_physical_seven_hex':post['physical_seven_hex'],
            'before_stack_q_window_28_hex':pre['stack_q_window_28_hex'],
            'after_stack_q_window_28_hex':post['stack_q_window_28_hex'],
            'source':'unchanged original probe pre/post bytes, never reconstructed from Core numeric fields'},
        'target_scope_complete':True, 'global_physical_closure_qualification_granted':False,
        'whole_core_NET_cause_proven':False, 'full_window_coverage_ready':False,
        'owner_admission_authority_verified_here':False}
    _need(len(_encoded(proof)) <= MAX_PROOF_BYTES, 'bounded explicit target proof; no whole Core replacement')
    return proof


def normalize_target_instruction_core_proof_12004(raw: bytes, binding: Mapping, *,
        target_core_proof: Mapping, parent_response: bytes, parent_proof: Mapping) -> dict:
    """Re-extract from original bytes; a standalone small proof never qualifies."""
    _need(isinstance(target_core_proof, Mapping) and len(_encoded(target_core_proof)) <= MAX_PROOF_BYTES and
          target_core_proof.get('schema') == PROOF_SCHEMA, 'bounded explicit target proof schema')
    path = target_core_proof.get('core_event_path')
    _need(type(path) is list, 'literal original Core event path')
    expected = build_target_instruction_core_proof_12004(parent_response=parent_response,
        parent_proof=parent_proof, binding=binding, core_event_path=tuple(path), raw=raw)
    _need(_encoded(dict(target_core_proof)) == _encoded(expected),
          'target proof exactly re-extracted from verified original full parent bytes, including JSON types')
    item, carrier, pre, _post, _start = _worker_wire(raw, binding)
    item.update(schema=ITEM_SCHEMA, native_core_token=carrier['invocation_token'],
        native_event_date_raw=carrier['date_raw'], same_core_invocation_join_ready=True,
        natural_attribution_ready=True, core_invocation_join_v1=expected['core_invocation_join'],
        core_carrier_v1=copy.deepcopy(pre['core_carrier_v1']),
        target_core_proof_v1=copy.deepcopy(expected),
        target_core_proof_canonical_derived_sha256=hashlib.sha256(_encoded(expected)).hexdigest(),
        full_parent_response_line_sha256=expected['full_parent']['response_line']['sha256'],
        global_physical_closure_qualification_granted=False,
        whole_core_NET_cause_proven=False, same_core_NET_cause_proven=False,
        full_window_coverage_ready=False, toggle_effect_proven=False,
        refill_business_qualification_granted=False, owner_admission_authority_verified_here=False)
    return item
