"""Lossless, bounded save-block projections for a single knight case.

Input is existing immutable Rakaly plaintext. This module performs no game,
desktop or provider operations. Duplicate keys and anonymous array items are
retained. A saved delta does not establish its precise runtime cause.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import re
from .knight_selector_replay import replay_selector_filters, candidate_words

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}=]|[^\s{}=]+')


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
            'death_killer_id': int(one(dead, 'killer')) if dead is not None and one(dead, 'killer') is not None else None}


def validate_scoped_journal(journal: dict | None, checkpoint: dict, victim: int,
                            related: int) -> dict:
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
    check('no truncated/failure journal', journal['truncated'] is False and journal['failure_flags'] == 0)
    check('global false retained', journal['global_mutable_bundle_complete'] is False)
    records = journal['records']
    check('nonempty records', bool(records))
    check('monotonic unique sequence', [r['sequence'] for r in records] == sorted({r['sequence'] for r in records}))
    dates = {checkpoint['before']['date_raw'], checkpoint['after']['date_raw']}
    check('every record same identity/date/thread', all(
        r['combat_id'] == journal['combat_id'] and r['failure_flags'] == 0 and
        r['native_date_raw'] in dates and r['thread_id'] == checkpoint['before']['thread_id'] for r in records))
    check('all typed character identities match', all(
        [c['character_id'] for c in r['characters']] == [victim, related] and all(
            c['identity_matches'] and c['observed_character_id'] == c['character_id'] for c in r['characters']) for r in records))
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
    if tuple_closed:
        request, commit = requests[0], commits[0]
        request_tuple = tuple(request['enter'][k] for k in tuple_fields)
        tuple_closed = request_tuple == tuple(commit['enter'][k] for k in tuple_fields) and \
            request_tuple[:3] == (victim, related, checkpoint['after']['date_raw']) and \
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
            all(c['death_marker_present'] and c['death_details_read'] and
                c['death_date_raw'] == checkpoint['after']['date_raw'] and
                 c['death_reason_key'] == 'death_battle' and c['death_killer_character_id'] == related for c in (after, final))
    artifact_tuple_closed = False
    if tuple_closed:
        events = [pair[edge] for pair in requests + enqueues + commits for edge in ('enter', 'return')]
        artifact_fields = ('requested_death_artifact_token', 'requested_death_artifact_id', 'requested_death_artifact_read')
        if all(all(k in row for k in artifact_fields) for row in events):
            first = tuple(events[0][k] for k in artifact_fields)
            artifact_tuple_closed = first[2] is True and all(tuple(row[k] for k in artifact_fields) == first for row in events)
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
            'death_commit_tuple_closed': tuple_closed,
            'death_artifact_tuple_closed': artifact_tuple_closed,
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
