"""Lossless, bounded save-block projections for a single knight case.

Input is existing immutable Rakaly plaintext. This module performs no game,
desktop or provider operations. Duplicate keys and anonymous array items are
retained. A saved delta does not establish its precise runtime cause.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
from .knight_selector_replay import replay_selector_filters, candidate_words

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}=]+')
DATE_CONTRACT_PATH = Path(__file__).with_name('data') / 'ck3_1_19_0_6_historical_date_layout_v1.json'


def decode_historical_date(raw64: int, *, expected_ticks: int | None = None,
                           saved_calendar: str | None = None, contract: dict | None = None) -> dict:
    """Decode the original full eight bytes and verify exact constructor caches."""
    if type(raw64) is not int or not -(1 << 63) <= raw64 < (1 << 63):
        raise ValueError('HistoricalDate requires original signed int64 full word')
    layout = json.loads(DATE_CONTRACT_PATH.read_text(encoding='utf-8')) if contract is None else contract
    tables = []
    for key, wanted in (('month_table', '218539A9F584E576A0912771D97AC39C5042FC9169E2B5D250069A88D1478F0A'),
                        ('day_table', '49CFA7734C595821C26DB19FAC8D0427FA12ADC3E8988E04E0D94198D8F35517')):
        table = layout[key]
        data = bytes.fromhex(table['hex'])
        if type(table['bytes']) is not int or table['bytes'] != len(data) or len(data) != 365 or \
                table['sha256'] != wanted or hashlib.sha256(data).hexdigest().upper() != wanted:
            raise ValueError('HistoricalDate exact constructor table identity mismatch')
        tables.append(data)
    if layout['epoch_ticks'] != 0x029C55C0 or layout['units_per_day'] != 24 or layout['days_per_year'] != 365 or \
            layout['executable_sha256'] != '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86':
        raise ValueError('HistoricalDate exact-build constants mismatch')
    raw = struct.pack('<q', raw64)
    ticks, day, month, year = struct.unpack('<iBBh', raw)
    difference = ticks - 0x029C55C0
    days = abs(difference) // 24 * (-1 if difference < 0 else 1)
    derived_year = abs(days) // 365 * (-1 if days < 0 else 1)
    day_of_year = days - derived_year * 365
    if not 0 <= day_of_year < 365 or not -(1 << 15) <= derived_year < (1 << 15):
        raise ValueError('HistoricalDate outside proven bounded constructor table range')
    if (day, month, year) != (tables[1][day_of_year], tables[0][day_of_year], derived_year):
        raise ValueError('HistoricalDate full-word cache disagrees with exact native constructor')
    calendar = f'{year}.{month + 1}.{day + 1}'
    if expected_ticks is not None and (type(expected_ticks) is not int or ticks != expected_ticks):
        raise ValueError('HistoricalDate signed ticks mismatch managed date')
    if saved_calendar is not None and (type(saved_calendar) is not str or calendar != saved_calendar):
        raise ValueError('HistoricalDate calendar mismatch same-run saved date')
    return {'raw64': raw64, 'full_hex_le': raw.hex().upper(), 'ticks_int32': ticks,
            'day_zero_based': day, 'month_zero_based': month, 'year_int16': year,
            'day_of_year_zero_based': day_of_year, 'calendar': calendar,
            'exact_constructor_cache_verified': True}


def decode_sparse_int32_vector(entries: list[dict], *, default: int = -1,
                               max_count: int = 256) -> list[int]:
    """The first anonymous integer is length; keyed indices override defaults."""
    if type(default) is not int or not -(1 << 31) <= default < (1 << 31) or \
            type(max_count) is not int or not 0 <= max_count <= 65536 or \
            not isinstance(entries, list) or not entries or entries[0].get('key') is not None:
        raise ValueError('sparse int32 vector requires original count header')
    def canonical(value: str) -> int:
        if type(value) is not str or re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value) is None:
            raise ValueError('sparse int32 vector canonical integer text required')
        result = int(value)
        if str(result) != value:
            raise ValueError('sparse int32 vector noncanonical integer')
        return result
    count = canonical(entries[0]['value'])
    if not 0 <= count <= max_count:
        raise ValueError('sparse int32 vector count out of bounds')
    values, seen = [default] * count, set()
    for entry in entries[1:]:
        index, value = canonical(entry['key']), canonical(entry['value'])
        if not 0 <= index < count or index in seen or not -(1 << 31) <= value < (1 << 31):
            raise ValueError('sparse int32 vector duplicate/index/value out of bounds')
        seen.add(index)
        values[index] = value
    return values


def classify_death_artifact_tuple(edges: list[dict], final_id: int | None,
                                  saved_id: int | None, *, saved_verified: bool = False) -> dict:
    """Keep measured null, invalid reference, valid ID and unknown reads separate."""
    fields = ('requested_death_artifact_token', 'requested_death_artifact_id', 'requested_artifact_id_read')
    if not edges or any(any(k not in r for k in fields) for r in edges):
        return {'closed': False, 'kind': 'unknown-missing-artifact-fields'}
    values = [tuple(r[k] for k in fields) for r in edges]
    pointer, identifier, read = values[0]
    if any(type(v[0]) is not str or re.fullmatch(r'process-local-0x[0-9a-f]+', v[0]) is None or
           type(v[1]) is not int or not -1 <= v[1] < (1 << 31) or type(v[2]) is not bool
           for v in values):
        raise ValueError('death artifact exact pointer/int32/bool types required')
    if any(v != values[0] for v in values):
        return {'closed': False, 'kind': 'unknown-mismatching-artifact-tuple'}
    address = int(pointer[len('process-local-'):], 16)
    if pointer != 'process-local-' + hex(address):
        raise ValueError('death artifact canonical original pointer token required')
    if address == 0:
        kind = 'verified-null' if identifier == -1 and read is False else 'unknown-inconsistent-null'
    elif read is False:
        kind = 'unknown-artifact-read'
    else:
        kind = 'nonnull-invalid-reference' if identifier == -1 else 'verified-full-id'
    if saved_verified and (type(final_id) is not int or final_id < -1 or
                           (saved_id is not None and type(saved_id) is not int)):
        raise ValueError('death artifact original final/save ID types required')
    expected = identifier if kind == 'verified-full-id' else -1
    consistency = saved_verified and final_id == expected and (
        saved_id == identifier if kind == 'verified-full-id' else saved_id in (None, -1))
    return {'closed': kind in ('verified-null', 'nonnull-invalid-reference', 'verified-full-id') and consistency,
            'kind': kind, 'requested_pointer': pointer, 'requested_id': identifier,
            'original_id_read': read, 'final_id': final_id, 'saved_id': saved_id,
            'same_run_saved_consistency_verified': bool(consistency),
            'fallback_pointer_identity_proven': False}


def validate_slain_side_knights_saved(journal: dict, before_blocks: list[dict],
                                      after_blocks: list[dict], victim: int) -> dict:
    """Compare original list writer bytes with the complete sparse save vector."""
    def check(ok: bool, why: str) -> None:
        if not ok:
            raise ValueError('slain saved list: ' + why)
    edges = [r for r in journal['records'] if r['boundary'] in ('list_write_enter', 'list_write_return') and
             r['variable_key'] == 'slain_side_knights']
    if not edges:
        return {'closed': False, 'status': 'NOT_CAPTURED'}
    check(len(edges) == 2 and [r['boundary'] for r in edges] == ['list_write_enter', 'list_write_return'],
          'one complete original declared writer pair')
    begin, end = edges
    check(begin['invocation'] == end['invocation'] and begin['parent_invocation'] == end['parent_invocation'] and
          begin['variable_owner_token'] == end['variable_owner_token'] and
          begin['variable_owner_scope_words'] == end['variable_owner_scope_words'] and
          all(r['variable_owner_from_original_getter'] is True and r['requested_character_full_identity_matches'] is True and
              r['requested_scope_words'] == [4, victim] and r['variable_list_read'] is True and
              type(r['requested_expiry']) is int and -(1 << 31) <= r['requested_expiry'] < (1 << 31) and
              type(r['list_elapsed_offset']) is int and -(1 << 31) <= r['list_elapsed_offset'] < (1 << 31)
              for r in edges) and begin['requested_expiry'] == end['requested_expiry'], 'actual getter owner/full-ID/expiry tuple')
    owner = begin['variable_owner_scope_words']
    check(len(owner) == 2 and all(type(v) is int for v in owner) and owner[0] & 0xFFFF == 11 and
          owner[1] == journal['combat_id'], 'original typed combatSide/full combat owner')
    side = (owner[0] >> 16) & 0xFFFF
    check(side in (0, 1), 'actual combat side index')
    side_name = ('attacker', 'defender')[side]
    def read_saved(blocks: list[dict]) -> dict:
        matches = []
        for combat in blocks:
            for block in find_key_blocks(combat['entries'], 'variables'):
                if not block['path'].endswith('/' + side_name + '[0]/variables[0]'):
                    continue
                lists = one(block['entries'], 'list')
                if lists is None:
                    continue
                for element in lists:
                    check(element['key'] is None and isinstance(element['value'], list), 'original anonymous named list object')
                    values = element['value']
                    if one(values, 'name') not in ('slain_side_knights', '"slain_side_knights"'):
                        continue
                    items = [e['value'] for e in values if e['key'] == 'item']
                    typed = []
                    for item in items:
                        check(isinstance(item, list) and one(item, 'type') == 'char', 'saved item original type char')
                        full_id = one(item, 'identity', required=True)
                        check(type(full_id) is str and re.fullmatch(r'(?:0|[1-9][0-9]*)', full_id) is not None and
                              0 < int(full_id) < (1 << 31), 'saved full-generation character identity')
                        typed.append([4, int(full_id)])
                    metadata = one(values, 'duration', required=True)
                    durations = decode_sparse_int32_vector(metadata)
                    check(len(durations) == len(typed), 'full sparse expiry count equals typed item count')
                    matches.append({'present': True, 'path': combat['path'] + block['path'],
                                    'scope_words': typed, 'decoded_expiry_values': durations,
                                    'original_sparse_duration_metadata': metadata, 'original_named_list_entries': values})
        check(len(matches) <= 1, 'unique saved scoped side/list')
        return matches[0] if matches else {'present': False, 'scope_words': [], 'decoded_expiry_values': []}
    before, after = read_saved(before_blocks), read_saved(after_blocks)
    for native, saved in ((begin, before), (end, after)):
        check(type(native['variable_list_present']) is bool and native['variable_list_present'] == saved['present'],
              'native/save list presence')
        actual = native['variable_list_values']
        check(all(type(v[k]) is int for v in actual for k in ('scope_word0', 'scope_word1', 'expiration_raw')),
              'native typed list item int32 words')
        words = [[v['scope_word0'], v['scope_word1']] for v in actual]
        expiries = [v['expiration_raw'] if v['expiration_raw'] == -1 else
                    v['expiration_raw'] - native['list_elapsed_offset'] for v in actual]
        check(words == saved['scope_words'] and expiries == saved['decoded_expiry_values'],
              'full native list and elapsed-adjusted expiry equal saved decoded vector')
    check(after['scope_words'] == before['scope_words'] + [[4, victim]], 'one actual victim typed append')
    expected = -1 if end['requested_expiry'] == -1 else end['requested_expiry'] + end['list_elapsed_offset']
    check(-(1 << 31) <= expected < (1 << 31) and end['variable_list_values'][-1]['expiration_raw'] == expected,
          'original append expiry respects -1 sentinel or elapsed adjustment')
    return {'closed': True, 'status': 'ORIGINAL_WRITER_AND_COMPLETE_SPARSE_SAVE_LIST_CHECKED',
            'owner_side_index': side, 'owner_full_combat_id': owner[1],
            'requested_expiry': end['requested_expiry'], 'native_elapsed_offset': end['list_elapsed_offset'],
            'before': before, 'after': after, 'duration_count_is_ttl': False,
            'limits': 'This validates this scoped list append and saved expiry vector, not all script variable writers.'}


def parse_block(body: str) -> list[dict]:
    tokens = TOKEN.findall(body)
    position = 0

    def value() -> str | list[dict]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError('truncated block value')
        token = tokens[position]
        position += 1
        if token != '{':
            if token in ('}', '='):
                raise ValueError('unexpected block token')
            return token
        entries = []
        while position < len(tokens) and tokens[position] != '}':
            key = None
            if position + 1 < len(tokens) and tokens[position + 1] == '=':
                key = tokens[position]
                position += 2
            entries.append({'key': key, 'value': value()})
        if position == len(tokens):
            raise ValueError('unterminated block')
        position += 1
        return entries

    parsed = value()
    if position != len(tokens) or not isinstance(parsed, list):
        raise ValueError('block was not consumed exactly')
    return parsed


def extract_exact_indented_block(text: str, key: str, depth: int) -> str:
    prefix = '\t' * depth
    pattern = rf'^{prefix}{re.escape(key)}=\{{\n(.*?)^{prefix}\}}'
    matches = list(re.finditer(pattern, text, re.M | re.S))
    if len(matches) != 1:
        raise ValueError(f'expected one block {key} at indentation {depth}; got {len(matches)}')
    return matches[0].group(0)


def block_body(raw: str) -> str:
    return raw[raw.index('{'):]


def flatten(entries: list[dict], prefix: str = '') -> dict[str, str | None]:
    leaves = {}
    counts: dict[str, int] = defaultdict(int)
    if not entries:
        leaves[prefix + '/{}'] = None
    for entry in entries:
        key = entry['key'] if entry['key'] is not None else '#array'
        ordinal = counts[key]
        counts[key] += 1
        path = f'{prefix}/{key}[{ordinal}]'
        if isinstance(entry['value'], list):
            leaves.update(flatten(entry['value'], path))
        else:
            leaves[path] = entry['value']
    return leaves


def delta(before: list[dict], after: list[dict]) -> list[dict]:
    left, right = flatten(before), flatten(after)
    return [{'path': path, 'before_present': path in left, 'before': left.get(path),
             'after_present': path in right, 'after': right.get(path)}
            for path in sorted(left.keys() | right.keys())
            if (path in left) != (path in right) or left.get(path) != right.get(path)]


def find_key_blocks(entries: list[dict], key: str, prefix: str = '') -> list[dict]:
    result = []
    counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        label = entry['key'] if entry['key'] is not None else '#array'
        ordinal = counts[label]
        counts[label] += 1
        path = f'{prefix}/{label}[{ordinal}]'
        if isinstance(entry['value'], list):
            if entry['key'] == key:
                result.append({'path': path, 'entries': entry['value']})
            result.extend(find_key_blocks(entry['value'], key, path))
    return result


def text_sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode('utf-8')).hexdigest().upper()


def one(entries: list[dict], key: str, *, required: bool = False):
    values = [entry['value'] for entry in entries if entry['key'] == key]
    if len(values) > 1 or (required and len(values) != 1):
        raise ValueError(f'nonunique or missing field {key}')
    return values[0] if values else None


def saved_death_artifact_evidence(dead_entries: list[dict] | None) -> dict:
    """Describe this saved block without inventing a positive artifact field.

    The exact-build ABI currently proves only the native signed ID and the
    case's complete dead_data containing the five already decoded fields.
    Any additional saved key needs its own ABI before absence can be used.
    """
    status = 'POSITIVE_ARTIFACT_SAVE_KEY_ABI_NOT_SUPPORTED'
    if dead_entries is None:
        return {'status': status, 'complete_known_fields_without_artifact': False,
                'saved_id': None, 'keys': []}
    if not isinstance(dead_entries, list) or any(not isinstance(r, dict) or
            type(r.get('key')) is not str or type(r.get('value')) is not str
            for r in dead_entries):
        raise ValueError('saved dead_data complete scalar entries required')
    keys = [r['key'] for r in dead_entries]
    if len(keys) != len(set(keys)):
        raise ValueError('saved dead_data duplicate fields')
    known = {'date', 'reason', 'killer', 'liege', 'liege_title'}
    absence = {'date', 'reason', 'killer'} <= set(keys) <= known
    return {'status': status, 'complete_known_fields_without_artifact': absence,
            'saved_id': None, 'keys': keys,
            'limits': 'No positive saved artifact key is inferred. Extra keys remain unsupported.'}


def character_snapshot(text: str, character_id: int) -> dict:
    raw = extract_exact_indented_block(text, str(character_id), 1)
    entries = parse_block(block_body(raw))
    alive, dead = one(entries, 'alive_data'), one(entries, 'dead_data')
    if (alive is None) == (dead is None):
        raise ValueError(f'character {character_id}: alive_data XOR dead_data required')
    lookup = re.findall(r'^traits_lookup=\{\s*\n\t([^\n]+)\n\}', text, re.M)
    if len(lookup) != 1:
        raise ValueError('unique saved trait lookup required')
    keys = lookup[0].split()
    indices = [int(row['value']) for row in one(entries, 'traits', required=True)]
    if len(indices) != len(set(indices)) or any(i < 0 or i >= len(keys) for i in indices):
        raise ValueError('invalid saved trait indices')
    skills = [int(row['value']) for row in one(entries, 'skill', required=True)]
    if len(skills) != 6:
        raise ValueError('saved base skill array requires six values')
    prestige = one(alive, 'prestige', required=True) if alive is not None else None
    court = one(entries, 'court_data')
    return {'character_id': character_id, 'raw_block': raw, 'entries': entries,
            'status': 'ALIVE' if alive is not None else 'DEAD',
            'base_skills': skills, 'trait_indices': indices,
            'trait_keys': [keys[i] for i in indices],
            'trait_lookup_sha256': text_sha256(lookup[0]),
            'prestige_currency': one(prestige, 'currency') if prestige is not None else None,
            'prestige_accumulated': one(prestige, 'accumulated') if prestige is not None else None,
            'regiment_id': int(one(court, 'regiment')) if court is not None and one(court, 'regiment') is not None else None,
            'house_id': int(one(entries, 'dynasty_house')) if one(entries, 'dynasty_house') is not None else None,
            'death_date': one(dead, 'date') if dead is not None else None,
            'death_reason': one(dead, 'reason') if dead is not None else None,
            'death_killer_id': int(one(dead, 'killer')) if dead is not None and one(dead, 'killer') is not None else None,
            'death_artifact_id': None,
            'death_artifact_saved_fields': saved_death_artifact_evidence(dead)}


def validate_scoped_thread_contract(journal: dict, checkpoint: dict,
                                   phase_trace: dict | None) -> dict:
    """Bind paused ownership and every engine callback to original phase reads.

    The exact-build publisher admits a phase boundary only when its original
    RNG owner equals GetCurrentThreadId(). Schedule/paused RNG owner zero is
    permitted there and must never be used to infer a phase executor.
    """
    def check(name: str, passed: bool) -> None:
        if not passed:
            raise ValueError('scoped thread contract: ' + name)

    before, after = checkpoint['before'], checkpoint['after']
    check('original phase trace required', isinstance(phase_trace, dict))
    check('paused owner and one day', all(
        type(s['thread_id']) is int and 0 < s['thread_id'] <= 0xFFFFFFFF and s['paused'] is True
        for s in (before, after)) and before['thread_id'] == after['thread_id'] and
        all(type(s['date_raw']) is int and type(s['pump_epoch']) is int and s['pump_epoch'] > 0
            for s in (before, after)) and after['pump_epoch'] > before['pump_epoch'] and
        after['date_raw'] == before['date_raw'] + 24 and
        before['combat_id'] == after['combat_id'] == journal['combat_id'] and
        before['managed_daily_sequence_token'] == after['managed_daily_sequence_token'] ==
        journal['managed_daily_sequence_token'])
    names = (
        'native_capture_before_side0_schedule_call_0x27FB58F',
        'native_capture_after_side1_schedule_return_0x27FB5AC',
        'native_capture_before_side0_phase_fire_entry_0x23C9900',
        'native_capture_after_side0_phase_fire_return_0x2309EF7',
        'native_capture_before_side1_phase_fire_entry_0x23C9900',
        'native_capture_after_side1_phase_fire_return_0x2309EFF',
        'paused_next_day_stable_query')
    ring = phase_trace['records']
    check('exact original flags0 seven phase boundaries', phase_trace['status'] == 'captured' and
          type(phase_trace['failure_flags']) is int and phase_trace['failure_flags'] == 0 and
          type(phase_trace['record_count']) is int and phase_trace['record_count'] == len(ring) == 7 and
          [r['boundary'] for r in ring] == list(names) and
          all(type(r['capture_failure_flags']) is int and r['capture_failure_flags'] == 0 and r['combat_id'] == journal['combat_id'] and
              r['managed_daily_sequence_token'] == journal['managed_daily_sequence_token'] and
              r['native_date_raw'] == (before if i < 2 else after)['date_raw'] and
              r['full_mutable_transition_bundle_complete'] is False for i, r in enumerate(ring)) and
          phase_trace['readiness']['full_mutable_transition_bundle_complete'] is False)
    check('original phase day split', type(ring[0]['phase_day']) is int and
          all(type(r['phase_day']) is int and r['phase_day'] ==
              ring[0]['phase_day'] + (0 if i < 2 else 1) for i, r in enumerate(ring)))
    worker = ring[2]['global_rng']['owner_thread_token']
    check('original phase executor', type(worker) is int and 0 < worker <= 0xFFFFFFFF and all(
        type(r['global_rng']['owner_thread_token']) is int and
        r['global_rng']['owner_thread_token'] == worker for r in ring[2:6]))
    rows = journal['records']
    check('contiguous journal sequence', all(type(r['sequence']) is int for r in rows) and
          [r['sequence'] for r in rows] == list(range(len(rows))))
    check('unique paused handoff boundaries', len(rows) >= 6 and
          rows[0]['boundary'] == 'arm_paused' and rows[-1]['boundary'] == 'next_paused' and
          sum(r['boundary'] == 'arm_paused' for r in rows) ==
          sum(r['boundary'] == 'next_paused' for r in rows) == 1)
    for row, stamp, phase in ((rows[0], before, ring[0]), (rows[-1], after, ring[6])):
        check('managed paused endpoint tuple', type(row['thread_id']) is int and
              row['thread_id'] == stamp['thread_id'] and row['native_date_raw'] == stamp['date_raw'] and
              row['phase_day'] == phase['phase_day'] and row['invocation'] == row['parent_invocation'] == 0 and
              row['side_index'] == row['native_event_load_index'] == -1)
    check('all actual process branches bind phase executor/date/day', all(
        type(r['thread_id']) is int and r['thread_id'] == worker and
        r['native_date_raw'] == after['date_raw'] and r['phase_day'] == ring[2]['phase_day']
        for r in rows[1:-1]))
    phase_rows = [r for r in rows if r['boundary'] in ('phase_before', 'phase_after')]
    check('four scoped phase edges match original ring', len(phase_rows) == 4 and all(
        r['boundary'] == ('phase_before' if i % 2 == 0 else 'phase_after') and
        r['side_index'] == i // 2 and r['invocation'] == r['parent_invocation'] == 0 and
        r['native_event_load_index'] == -1 and r['thread_id'] ==
        ring[i + 2]['global_rng']['owner_thread_token'] and
        r['native_date_raw'] == ring[i + 2]['native_date_raw'] and
        r['phase_day'] == ring[i + 2]['phase_day'] for i, r in enumerate(phase_rows)))
    kinds = {'effect', 'filter', 'materializer', 'predicate', 'selector', 'list_write',
             'death_request', 'death_enqueue', 'death_commit', 'casualty'}
    allowed = {'arm_paused', 'next_paused', 'phase_before', 'phase_after'} | {
        kind + '_' + edge for kind in kinds for edge in ('enter', 'return')}
    check('original typed boundary names and invocation types', all(
        r['boundary'] in allowed and type(r['invocation']) is int and r['invocation'] >= 0 and
        type(r['parent_invocation']) is int and r['parent_invocation'] >= 0 and
        type(r['side_index']) is int and r['side_index'] in (-1, 0, 1) and
        type(r['native_event_load_index']) is int and
        r['native_event_load_index'] == (journal['event_load_index'] if
            r['boundary'].rsplit('_', 1)[0] in
            {'effect', 'filter', 'materializer', 'predicate', 'selector', 'list_write'} else -1)
        for r in rows))
    pairs = {}
    for row in rows:
        if row['boundary'].endswith(('_enter', '_return')):
            kind, edge = row['boundary'].rsplit('_', 1)
            check('nonzero typed invocation', row['invocation'] > 0)
            pair = pairs.setdefault((kind, row['invocation']), {})
            check('no duplicate invocation edge', edge not in pair)
            pair[edge] = row
    fields = ('thread_id', 'native_date_raw', 'phase_day', 'combat_id', 'side_index',
              'native_event_load_index', 'parent_invocation')
    check('complete invocation pairs preserve actual tuple', all(
        set(p) == {'enter', 'return'} and p['enter']['sequence'] < p['return']['sequence'] and
        all(p['enter'][k] == p['return'][k] for k in fields) for p in pairs.values()))
    allocated = [invocation for (kind, invocation) in pairs if kind not in ('selector', 'materializer')]
    check('fresh allocated invocation IDs unique across kinds', len(allocated) == len(set(allocated)))
    intervals = [(kind, invocation, p['enter'], p['return']) for (kind, invocation), p in pairs.items()]
    check('original invocation nesting', all(not (
        a['sequence'] < c['sequence'] < b['sequence'] < d['sequence'])
        for _, _, a, b in intervals for _, _, c, d in intervals))
    for kind, invocation, entry, returned in intervals:
        parent = entry['parent_invocation']
        if kind in ('casualty', 'death_commit'):
            check('post-phase standalone branch', parent == 0 and
                  phase_rows[-1]['sequence'] < entry['sequence'] < returned['sequence'] < rows[-1]['sequence'])
            continue
        phase = [i for i in (0, 2) if phase_rows[i]['sequence'] < entry['sequence'] <
                 returned['sequence'] < phase_rows[i + 1]['sequence']]
        check('typed call stays inside actual phase', len(phase) == 1 and
              (entry['side_index'] == -1 or entry['side_index'] == phase[0] // 2))
        if kind == 'effect' and parent == 0:
            check('root effect depth', entry['depth'] == returned['depth'] == 0)
            continue
        # SelectorCapture stamps the active effect ID even for predicates;
        # filter invocation is an independently bounded enclosing call.
        parent_kind = 'death_request' if kind == 'death_enqueue' else 'effect'
        ancestor = pairs.get((parent_kind, parent))
        check('same-thread actual parent invocation', ancestor is not None and
              ancestor['enter']['sequence'] < entry['sequence'] < returned['sequence'] < ancestor['return']['sequence'] and
              ancestor['enter']['thread_id'] == entry['thread_id'])
        if kind == 'effect':
            check('effect depth and side ancestry', entry['depth'] == returned['depth'] ==
                  ancestor['enter']['depth'] + 1 and entry['side_index'] == ancestor['enter']['side_index'])
        if kind == 'selector':
            check('selector uses active effect invocation', invocation == parent)
        if kind in ('predicate', 'materializer'):
            enclosing = [p for (name, _), p in pairs.items() if name == 'filter' and
                         p['enter']['parent_invocation'] == parent and
                         p['enter']['sequence'] < entry['sequence'] < returned['sequence'] < p['return']['sequence']]
            check('selector child stays inside actual filter', len(enclosing) == 1)
            if kind == 'materializer':
                check('materializer inherits enclosing filter invocation', invocation == enclosing[0]['enter']['invocation'])
    return {'status': 'ORIGINAL_THREAD_ROLES_CHECKED', 'managed_owner_thread_id': before['thread_id'],
            'phase_executor_thread_id': worker, 'paused_endpoint_count': 2,
            'phase_edge_count': 4, 'process_record_count': len(rows) - 2,
            'source_of_executor': 'flags0 original ring phase global_rng.owner_thread_token; publisher requires actual GetCurrentThreadId equality'}


def validate_scoped_journal(journal: dict | None, checkpoint: dict, victim: int,
                            related: int, phase_trace: dict | None = None, *,
                            saved_victim: dict | None = None) -> dict:
    """Verify actual typed sequence and report remaining domains, without approval.

    This verifies the captured case tuple, not a proposition that CK3 has only
    one death mechanism. Missing typed evidence returns an explicit gap.
    """
    if journal is None:
        return {'status': 'NOT_CAPTURED', 'death_commit_tuple_closed': False,
                'global_bundle_complete': False, 'full_mutable_transition_bundle_complete': False,
                'gaps': ['scoped_transition_chain absent in this source/run']}
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({'name': name, 'pass': passed})
        if not passed:
            raise ValueError('scoped journal: ' + name)

    check('schema1', journal['schema_version'] == 1)
    check('two declared full character IDs', journal['character_ids'] == [victim, related])
    check('same combat', journal['combat_id'] == checkpoint['before']['combat_id'])
    check('same managed daily token', journal['managed_daily_sequence_token'] == checkpoint['before']['managed_daily_sequence_token'])
    check('no truncated/failure journal', journal['truncated'] is False and
          type(journal['failure_flags']) is int and journal['failure_flags'] == 0)
    check('global false retained', journal['global_mutable_bundle_complete'] is False)
    records = journal['records']
    check('nonempty records', bool(records))
    check('monotonic unique sequence', [r['sequence'] for r in records] == sorted({r['sequence'] for r in records}))
    dates = {checkpoint['before']['date_raw'], checkpoint['after']['date_raw']}
    check('every record same identity/date', all(
        type(r['combat_id']) is int and r['combat_id'] == journal['combat_id'] and
        type(r['failure_flags']) is int and r['failure_flags'] == 0 and
        type(r['native_date_raw']) is int and r['native_date_raw'] in dates for r in records))
    thread_contract = validate_scoped_thread_contract(journal, checkpoint, phase_trace)
    check('all typed character identities match', all(
        [c['character_id'] for c in r['characters']] == [victim, related] and all(
            type(c['character_id']) is int and type(c['observed_character_id']) is int and
            c['identity_matches'] is True and c['observed_character_id'] == c['character_id']
            for c in r['characters']) for r in records))
    pairs = {}
    for record in records:
        boundary = record['boundary']
        if boundary.endswith('_enter') or boundary.endswith('_return'):
            if record['invocation'] <= 0:
                raise ValueError('zero typed invocation')
            kind, end = boundary.rsplit('_', 1)
            key = (kind, record['invocation'])
            pair = pairs.setdefault(key, {})
            if end in pair:
                raise ValueError('duplicate invocation edge')
            pair[end] = record
    check('all invocation enter/return pairs complete', all(
        set(pair) == {'enter', 'return'} and pair['enter']['sequence'] < pair['return']['sequence'] and
        pair['enter']['parent_invocation'] == pair['return']['parent_invocation']
        for pair in pairs.values()))
    check('arm through final paused', records[0]['boundary'] == 'arm_paused' and
          records[-1]['boundary'] == 'next_paused' and records[0]['native_date_raw'] == checkpoint['before']['date_raw'] and
          records[-1]['native_date_raw'] == checkpoint['after']['date_raw'])
    requests = [pair for (kind, _), pair in pairs.items() if kind == 'death_request' and pair['enter']['death_victim_id'] == victim]
    commits = [pair for (kind, _), pair in pairs.items() if kind == 'death_commit' and pair['enter']['death_victim_id'] == victim]
    enqueues = [pair for (kind, _), pair in pairs.items() if kind == 'death_enqueue' and pair['enter']['death_victim_id'] == victim]
    tuple_closed = len(requests) == len(commits) == 1 and len(enqueues) <= 1
    tuple_fields = ('death_victim_id', 'death_killer_id', 'requested_death_date_raw', 'requested_death_reason_token')
    typed_date = None
    artifact_evidence = {'closed': False, 'kind': 'pending'}
    if tuple_closed:
        request, commit = requests[0], commits[0]
        edges = [p[e] for p in requests + enqueues + commits for e in ('enter', 'return')]
        request_tuple = tuple(request['enter'][k] for k in tuple_fields)
        typed_date = decode_historical_date(request_tuple[2], expected_ticks=checkpoint['after']['date_raw'],
            saved_calendar=saved_victim['death_date'] if saved_victim is not None else None)
        tuple_closed = all(tuple(r[k] for k in tuple_fields) == request_tuple for r in edges) and \
            request_tuple[:2] == (victim, related) and \
            request['enter']['sequence'] < commit['enter']['sequence']
        if enqueues:
            enqueue = enqueues[0]
            tuple_closed = tuple_closed and request_tuple == tuple(enqueue['enter'][k] for k in tuple_fields) and \
                request['enter']['sequence'] < enqueue['enter']['sequence'] < enqueue['return']['sequence'] < commit['enter']['sequence'] and \
                enqueue['return']['death_queue_count'] == enqueue['enter']['death_queue_count'] + 1
        before = commit['enter']['characters'][0]
        after = commit['return']['characters'][0]
        final = records[-1]['characters'][0]
        tuple_closed = tuple_closed and before['death_marker_present'] is False and \
            all(c['death_marker_present'] is True and c['death_details_read'] is True and
                type(c['death_date_raw']) is int and c['death_date_raw'] == request_tuple[2] and
                 c['death_reason_key'] == 'death_battle' and c['death_killer_character_id'] == related for c in (after, final))
        if tuple_closed:
            for c in (after, final):
                decode_historical_date(c['death_date_raw'], expected_ticks=checkpoint['after']['date_raw'],
                    saved_calendar=saved_victim['death_date'] if saved_victim is not None else None)
        saved_verified = saved_victim is not None and saved_victim['character_id'] == victim and \
            saved_victim['status'] == 'DEAD' and saved_victim['death_date'] == typed_date['calendar'] and \
            saved_victim['death_reason'] in ('death_battle', '"death_battle"') and saved_victim['death_killer_id'] == related
        tuple_closed = tuple_closed and saved_verified
        saved_artifact = saved_death_artifact_evidence(
            one(saved_victim['entries'], 'dead_data') if saved_victim is not None else None)
        artifact_evidence = classify_death_artifact_tuple(edges, final.get('death_artifact_id'),
            saved_artifact['saved_id'], saved_verified=bool(saved_verified) and
            saved_artifact['complete_known_fields_without_artifact'] is True)
        artifact_evidence['saved_field_evidence'] = saved_artifact
    artifact_tuple_closed = False
    artifact_tuple_kind = 'pending'
    if tuple_closed:
        artifact_tuple_closed = artifact_evidence['closed']
        artifact_tuple_kind = artifact_evidence['kind']
    selectors = [pair for (kind, _), pair in pairs.items() if kind == 'selector']
    selected_member_closed = len(selectors) == 1
    selected_index = None
    if selected_member_closed:
        selected = selectors[0]['return']
        candidates = selected.get('selector_candidates', [])
        selected_index = selected.get('selected_candidate_index')
        selected_member_closed = type(selected_index) is int and 0 <= selected_index < len(candidates) and all(
            row.get('scope_word0', -1) & 0xFFFF == 4 and row.get('character_full_identity_matches') is True and
            type(row.get('character_id')) is int and row['character_id'] > 0 for row in candidates)
        if selected_member_closed:
            selected_member_closed = candidates[selected_index]['character_id'] == related
    native_death_path_closed = False
    if tuple_closed and selected_member_closed:
        request = requests[0]['enter']
        effect = pairs.get(('effect', request['parent_invocation']))
        native_death_path_closed = effect is not None and \
            effect['enter'].get('node_vtable_rva') == 0x4468B28 and \
            effect['enter']['sequence'] < request['sequence'] < effect['return']['sequence'] and \
            selectors[0]['return']['sequence'] < request['sequence'] and \
            request.get('caller_return_token', 0) != 0
    filter_replay = replay_selector_filters(journal)
    materializer_filter_complete = False
    if filter_replay['complete'] and selected_member_closed:
        selected = selectors[0]
        matching = [f for f in filter_replay['filters'] if
                    f['parent_invocation'] == selected['enter']['invocation'] and
                    f['sequence_return'] < selected['enter']['sequence'] and
                    f['final_raw_words'] == [list(w) for w in candidate_words(selected['enter'])] and
                    f['final_raw_words'] == [list(w) for w in candidate_words(selected['return'])]]
        materializer_filter_complete = len(matching) == 1
    gaps = []
    if not tuple_closed:
        gaps.append('single case request/queue/commit tuple and final typed death fields not closed')
    if not selected_member_closed:
        gaps.append('complete typed post-filter candidate vector/index/selected related character not closed')
    if not native_death_path_closed:
        gaps.append('typed death request ancestry to actual CCharacterDeathEffect not closed')
    if not artifact_tuple_closed:
        gaps.append('request/queue/commit artifact null-or-full-ID tuple not independently closed')
    if not materializer_filter_complete:
        gaps.append('original materializer/filter/predicate/tail-swap replay not uniquely connected to actual selected vector')
    unpublished = journal.get('domain_coverage', {}).get('unpublished_intraday_values', [])
    if unpublished:
        gaps.append('no typed intraday values: ' + ', '.join(unpublished))
    return {'status': 'CAPTURED_TYPED_SEQUENCE_CHECKED', 'checks': checks,
            'thread_contract': thread_contract,
            'death_commit_tuple_closed': tuple_closed,
            'death_date_typed_evidence': typed_date,
            'death_artifact_tuple_closed': artifact_tuple_closed,
            'death_artifact_tuple_kind': artifact_tuple_kind,
            'death_artifact_evidence': artifact_evidence,
            'selector_post_filter_selected_member_closed': selected_member_closed,
            'selected_candidate_index': selected_index,
            'materializer_filter_complete': materializer_filter_complete,
            'selector_filter_replay': filter_replay,
            'case_native_death_execution_path_closed': native_death_path_closed,
            'victim_request_count': len(requests), 'victim_enqueue_count': len(enqueues),
            'victim_commit_count': len(commits), 'required_write_domains': journal.get('required_write_domains', []),
            'domain_coverage': journal.get('domain_coverage', {}),
            'global_bundle_complete': False, 'full_mutable_transition_bundle_complete': False,
            'sole_cause_proven': False, 'gaps': gaps,
            'limits': 'A matching single observed native commit is case-path evidence. It is not full mutable per-write causality, UI approval, or a global unique death-mechanism claim.'}
