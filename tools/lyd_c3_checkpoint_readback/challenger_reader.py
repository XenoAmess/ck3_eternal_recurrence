"""Read-only bounded CK3 checkpoint projection; never a native business verdict.

Actual save execution requires a fully bound ROOT request. An unbound request
fails before opening a save. Unknown native serialization remains UNKNOWN.
The pinned parser is reused unchanged behind strict lexical/resource guards.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'dependencies'))
from bounded_save_parser import TOKEN, parse_block, one, extract_exact_indented_block, block_body
from save_fields import stored, unquote

SOURCE_HEAD = '632f0a57a07aa6299052004589ed6f7632e7d8f7'
MAX_SAVE_BYTES = 256 * 1024 * 1024
MAX_BLOCK_BYTES = 24 * 1024 * 1024
MAX_TOKENS = 2_000_000
MAX_DEPTH = 128
MAX_TITLES = 60_000
MAX_ROLES = 256
MAX_CHALLENGERS = 128
INVALID = {'0', '4294967295'}

class ReadError(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def strict_json(raw):
    def unique(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ReadError('duplicate JSON field: ' + key)
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)

def identifier(value, label, allow_zero=False):
    pattern = r'(?:0|[1-9][0-9]*)' if allow_zero else r'[1-9][0-9]*'
    if not isinstance(value, str) or not re.fullmatch(pattern, value) or int(value) >= 4294967295:
        raise ReadError('invalid typed object identity: ' + label)
    return value

def pointer(rows, key):
    value = one(rows, key)
    if value is None:
        return {'status': 'MISSING', 'identity': None}
    if not isinstance(value, str):
        raise ReadError('non-scalar native pointer: ' + key)
    if value in INVALID:
        return {'status': 'INVALID_SENTINEL', 'identity': None, 'raw': value}
    return {'status': 'VALUE', 'identity': identifier(value, key)}

def require_pointer(rows, key):
    result = pointer(rows, key)
    if result['status'] != 'VALUE':
        raise ReadError('required native pointer absent: ' + key)
    return result['identity']

def bounded_parse(raw):
    if len(raw.encode('utf-8')) > MAX_BLOCK_BYTES:
        raise ReadError('block byte limit exceeded')
    depth, count, end = 0, 0, 0
    for match in TOKEN.finditer(raw):
        if raw[end:match.start()].strip():
            raise ReadError('unconsumed lexical input')
        token = match.group()
        if token.startswith('"'):
            if not token.endswith('"') or len(token) < 2:
                raise ReadError('unterminated quoted scalar')
            try:
                json.loads(token)
            except ValueError as error:
                raise ReadError('unsupported quoted scalar encoding') from error
        elif '#' in token or '"' in token:
            raise ReadError('unqualified comment/quote syntax')
        depth += (token == '{') - (token == '}')
        if depth < 0 or depth > MAX_DEPTH:
            raise ReadError('brace depth outside qualified bound')
        count += 1
        if count > MAX_TOKENS:
            raise ReadError('block token limit exceeded')
        end = match.end()
    if raw[end:].strip() or depth != 0:
        raise ReadError('unbalanced or unconsumed block')
    return parse_block(raw)

def exact_block(text, key, depth=0):
    raw = extract_exact_indented_block(text, str(key), depth)
    return bounded_parse(block_body(raw))

def section(text, key, following):
    a = list(re.finditer(r'(?m)^' + re.escape(key) + r'=\{\n', text))
    b = list(re.finditer(r'(?m)^' + re.escape(following) + r'=\{\n', text))
    if len(a) != 1 or len(b) != 1 or a[0].start() >= b[0].start():
        raise ReadError('missing/ambiguous qualified section: ' + key)
    return text[a[0].start():b[0].start()]

def record_index(text, maximum=MAX_TITLES):
    """Index qualified depth-zero record spans once; no per-ID world re-scan."""
    starts = list(re.finditer(r'(?m)^([0-9]+)=\{\n', text))
    if len(starts) > maximum:
        raise ReadError('record index bound exceeded')
    result = {}
    for index, match in enumerate(starts):
        ident = identifier(match.group(1), 'native record', allow_zero=True)
        if ident in result:
            raise ReadError('duplicate native record identity')
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        chunk = text[match.start():end]
        result[ident] = extract_exact_indented_block(chunk, ident, 0)
    return result

def database(text, key):
    rows = one(exact_block(text, key), 'database', required=True)
    if not isinstance(rows, list):
        raise ReadError('non-block database: ' + key)
    result = {}
    for row in rows:
        if row['key'] is None or not str(row['key']).isdigit() or not isinstance(row['value'], list):
            raise ReadError('unknown database record shape: ' + key)
        ident = identifier(row['key'], key, allow_zero=True)
        if ident in result:
            raise ReadError('duplicate database identity: ' + ident)
        result[ident] = row['value']
    if len(result) > MAX_TITLES:
        raise ReadError('database object limit exceeded')
    return result

def typed_var(variables, name, kind, required=True):
    row = variables.get(name)
    if row is None:
        if required:
            raise ReadError('missing typed variable: ' + name)
        return None
    if row['type'] != kind:
        raise ReadError('wrong typed variable scope: ' + name)
    return identifier(row['identity'], name, allow_zero=kind in {'faith', 'rite'})

def number(variables, name, required=True):
    row = variables.get(name)
    if row is None:
        if required:
            raise ReadError('missing saved number: ' + name)
        return None
    if row['type'] != 'value' or 'number' not in row:
        raise ReadError('wrong saved number type: ' + name)
    return str(Decimal(row['number']))

def typed_list(lists, name, kind, required=True):
    row = lists.get(name)
    if row is None:
        if required:
            raise ReadError('missing typed list: ' + name)
        return None
    items = []
    for item in row['items']:
        if item['type'] != kind:
            raise ReadError('mixed/wrong typed list: ' + name)
        ident = identifier(item['identity'], name)
        if ident in items:
            raise ReadError('duplicate list member: ' + name)
        items.append(ident)
    return items

def path_values(rows, path):
    if not isinstance(path, list) or not path or not all(isinstance(x, str) and x for x in path):
        raise ReadError('explicit native field path required')
    current = rows
    for key in path[:-1]:
        current = one(current, key, required=True)
        if not isinstance(current, list):
            raise ReadError('native path traverses scalar')
    return [row['value'] for row in current if row['key'] == path[-1]]

def collection(rows, binding):
    if binding is None:
        return {'status': 'UNKNOWN_SERIALIZATION', 'items': None, 'raw_values': None}
    if binding.get('encoding') not in {'repeated_scalar', 'anonymous_scalars', 'anonymous_records'}:
        raise ReadError('unqualified native collection encoding')
    values = path_values(rows, binding['path'])
    if not values:
        if binding.get('absence_means_empty') is True:
            return {'status': 'QUALIFIED_ABSENT_EMPTY', 'items': [], 'raw_values': []}
        raise ReadError('qualified native collection field missing')
    encoding = binding['encoding']
    if encoding == 'repeated_scalar':
        ids = [identifier(value, 'challenger title') for value in values]
    else:
        if len(values) != 1 or not isinstance(values[0], list):
            raise ReadError('ambiguous/non-block native collection')
        ids = []
        for row in values[0]:
            if row['key'] is not None:
                raise ReadError('unknown keyed collection item')
            if encoding == 'anonymous_scalars':
                ident = identifier(row['value'], 'challenger title')
            elif encoding == 'anonymous_records':
                if not isinstance(row['value'], list):
                    raise ReadError('non-record native collection member')
                selected = path_values(row['value'], binding['item_title_path'])
                if len(selected) != 1:
                    raise ReadError('nonunique challenger title within native record')
                ident = identifier(selected[0], 'challenger title')
            else:
                raise ReadError('unqualified native collection encoding')
            ids.append(ident)
    if len(ids) > MAX_CHALLENGERS:
        raise ReadError('native challenger collection bound exceeded')
    if len(set(ids)) != len(ids):
        raise ReadError('duplicate native challenger Title; raw input retained by projection source')
    return {'status': 'QUALIFIED_EXPLICIT', 'items': ids, 'raw_values': values}

def title_row(ident, rows):
    variables, lists, _ = stored(rows)
    holder = pointer(rows, 'holder')
    return {'title_id': ident, 'holder': holder, 'holder_id': holder['identity'], 'entries': rows, 'AST_sha256': digest(rows), 'variables': variables, 'lists': lists, 'qualification': {'law': 'UNKNOWN', 'native_properties': 'UNKNOWN'}}

def saved_title_ref(snapshot, name, required=True):
    kind = snapshot['qualification']['saved_title_scope_type']
    if kind is None:
        raise ReadError('saved Title scope typename unqualified')
    return typed_var(snapshot['actor_variables'], name, kind, required)

def project(text, actor_id, incumbent_id, political_ids, binding=None, watch_character_ids=None, watch_title_ids=None):
    """Pure function for exact plaintext/frozen serializer, used by bounded fixtures."""
    text = text.replace('\r\n', '\n')
    if len(text.encode()) > MAX_SAVE_BYTES:
        raise ReadError('save byte limit exceeded')
    actor_id, incumbent_id = identifier(str(actor_id), 'actor'), identifier(str(incumbent_id), 'incumbent')
    political_ids = [identifier(str(i), 'political Title') for i in political_ids]
    if len(political_ids) != 7 or len(set(political_ids)) != 7:
        raise ReadError('exact explicit7 political Title identities required')
    meta, played = exact_block(text, 'meta_data'), exact_block(text, 'played_character')
    if unquote(one(meta, 'version', required=True)) != '1.20.0.3' or one(meta, 'save_game_version', required=True) != '17':
        raise ReadError('unqualified save version')
    if one(played, 'character', required=True) != actor_id:
        raise ReadError('saved player differs from explicit actor')
    dates = re.findall(r'(?m)^date=([^\n]+)$', text)
    controls = re.findall(r'(?m)^currently_played_characters=(\{[^\n]*\})$', text)
    if len(dates) != 1 or len(controls) != 1 or one(meta, 'meta_date', required=True) != dates[0]:
        raise ReadError('qualified saved date/control rows missing or ambiguous')
    control_rows = bounded_parse(controls[0])
    control_ids = [identifier(row['value'], 'current controller') for row in control_rows if row['key'] is None]
    if len(control_ids) != len(control_rows) or len(set(control_ids)) != len(control_ids) or actor_id not in control_ids:
        raise ReadError('saved actor control list malformed/inconsistent')
    faiths, rites = database(text, 'faiths'), database(text, 'rites')
    parents = {i: identifier(one(rows, 'faith', required=True), 'native Rite parent Faith', allow_zero=True) for i, rows in rites.items()}
    mains = {}
    for ident, rows in faiths.items():
        value = one(rows, 'main_rite')
        if value is not None and isinstance(value, str) and value in rites:
            mains[ident] = {'status': 'VALUE', 'identity': value}
        else:
            mains[ident] = pointer(rows, 'main_rite')
    living = section(text, 'living', 'dead_unprunable')
    living_index = record_index(living)
    if actor_id not in living_index:
        raise ReadError('actual actor record missing')
    actor = bounded_parse(block_body(living_index[actor_id]))
    alive = one(actor, 'alive_data', required=True)
    if not isinstance(alive, list):
        raise ReadError('actor alive_data missing')
    av, al, _ = stored(alive)
    rid = require_pointer(actor, 'rite')
    if rid not in parents or parents[rid] not in faiths:
        raise ReadError('actor Rite/Faith not in native graph')
    fid = parents[rid]
    title_kind = binding.get('title_variable_type') if binding else None
    if title_kind is not None and (not isinstance(title_kind, str) or not title_kind or title_kind in {'char', 'faith', 'rite', 'value', 'boolean'}):
        raise ReadError('unqualified/mismatched saved Title scope typename')
    head_reference = av.get('lyd_i3b_result_head_title')
    head_title = typed_var(av, 'lyd_i3b_result_head_title', title_kind, required=False) if title_kind else None
    selected_faiths = {fid}
    for row in av.values():
        if row['type'] == 'faith' and row['identity'] != '4294967295':
            selected_faiths.add(identifier(row['identity'], 'stored owner Faith', allow_zero=True))
    if not selected_faiths.issubset(faiths):
        raise ReadError('typed owner Faith record missing')
    selected_faith_rows = {}
    challenger_ids = []
    for ident in sorted(selected_faiths, key=int):
        rows = faiths[ident]
        vs, ls, _ = stored(rows)
        coll = collection(rows, binding['collection'] if binding else None)
        selected_faith_rows[ident] = {'entries': rows, 'AST_sha256': digest(rows), 'variables': vs, 'lists': ls, 'HoF': pointer(rows, 'religious_head'), 'head_title': pointer(rows, 'religious_head_title'), 'main': mains[ident], 'native_challengers': coll}
        if coll['items'] is not None:
            challenger_ids.extend(coll['items'])
    current_rites = {i: rows for i, rows in rites.items() if parents[i] == fid}
    selected_rites = {}
    for ident, rows in current_rites.items():
        vs, ls, _ = stored(rows)
        selected_rites[ident] = {'entries': rows, 'AST_sha256': digest(rows), 'variables': vs, 'lists': ls, 'parent_faith': fid, 'HoR': pointer(rows, 'head_of_rite')}
    watched_titles = {identifier(str(i), 'watched previous Title') for i in watch_title_ids or []}
    target_ids = set(political_ids) | set(challenger_ids)
    if head_title:
        target_ids.add(head_title)
    for row in selected_faith_rows.values():
        if row['head_title']['identity']:
            target_ids.add(row['head_title']['identity'])
    for row in av.values():
        if title_kind and row['type'] == title_kind and row['identity'] not in INVALID:
            target_ids.add(identifier(row['identity'], 'stored Title'))
    title_section = section(text, 'landed_titles', 'dynasties')
    title_index = record_index(title_section)
    title_keys = list(title_index)
    titles, npc_titles = {}, []
    current_legitimate = selected_faith_rows[fid]['head_title']['identity']
    for ident in title_keys:
        rows = bounded_parse(block_body(title_index[ident]))
        holder = pointer(rows, 'holder')
        if ident in target_ids or ident in watched_titles or holder['identity'] in {actor_id, incumbent_id}:
            row = title_row(ident, rows)
            titles[ident] = row
            if holder['identity'] == incumbent_id and ident != current_legitimate:
                npc_titles.append(row)
    if not target_ids.issubset(titles):
        raise ReadError('referenced native Title record missing: ' + ','.join(sorted(target_ids - set(titles))))
    if len(titles) > MAX_ROLES:
        raise ReadError('selected title bound exceeded')
    sponsor_values = {}
    if binding and binding.get('sponsor_title_path'):
        for ident in challenger_ids:
            values = path_values(titles[ident]['entries'], binding['sponsor_title_path'])
            if len(values) != 1:
                raise ReadError('challenger sponsor missing/nonunique')
            sponsor_values[ident] = identifier(values[0], 'native sponsor Title')
            if sponsor_values[ident] not in title_keys:
                raise ReadError('native sponsor Title record missing')
            if sponsor_values[ident] not in titles:
                titles[sponsor_values[ident]] = title_row(sponsor_values[ident], bounded_parse(block_body(title_index[sponsor_values[ident]])))
    if len(titles) > MAX_ROLES:
        raise ReadError('selected title/sponsor bound exceeded')
    role_ids = {actor_id, incumbent_id} | {identifier(str(i), 'watched previous character') for i in watch_character_ids or []}
    for row in selected_faith_rows.values():
        if row['HoF']['identity']:
            role_ids.add(row['HoF']['identity'])
    for row in selected_rites.values():
        if row['HoR']['identity']:
            role_ids.add(row['HoR']['identity'])
    for row in titles.values():
        if row['holder']['identity']:
            role_ids.add(row['holder']['identity'])
    for name in ('lyd_c3_players', 'lyd_i3b_humans'):
        values = typed_list(al, name, 'char', required=False)
        if values:
            role_ids.update(values)
    if len(role_ids) > MAX_ROLES:
        raise ReadError('character role bound exceeded')
    chars = {}
    for ident in sorted(role_ids, key=int):
        if ident not in living_index:
            raise ReadError('referenced live character record missing')
        rows = actor if ident == actor_id else bounded_parse(block_body(living_index[ident]))
        ca = one(rows, 'alive_data', required=True)
        if not isinstance(ca, list):
            raise ReadError('referenced character is not live')
        vs, ls, _ = stored(ca)
        rite = require_pointer(rows, 'rite')
        if rite not in parents:
            raise ReadError('referenced character Rite missing')
        chars[ident] = {'character_id': ident, 'rite_id': rite, 'faith_id': parents[rite], 'entries': rows, 'AST_sha256': digest(rows), 'variables': vs, 'lists': ls}
    protections = [dict(titles[i], baseline_AST_sha256=titles[i]['AST_sha256'], baseline_holder=titles[i]['holder']) for i in political_ids]
    return {
        'schema': 'lyd.c3.bounded-native-checkpoint-state.v1',
        'identity': {'actor_id': actor_id, 'incumbent_id': incumbent_id, 'faith_id': fid, 'rite_id': rid, 'I3b_result_head_title': head_title, 'saved_date': dates[0], 'current_controller_ids': control_ids},
        'faiths': selected_faith_rows, 'rites': selected_rites, 'all_faith_mains': mains, 'all_rite_parents': parents,
        'characters': chars, 'actor_variables': av, 'actor_lists': al,
        'actor_landed_data': one(actor, 'landed_data'),
        'result_head_title_reference': head_reference,
        'native_title': titles.get(head_title) if head_title else None,
        'partial_native_title': titles.get(selected_faith_rows[fid]['head_title']['identity']) if head_title is None else None,
        'titles': titles, 'native_challenger_titles': [titles[i] for i in challenger_ids],
        'all_title_record_ids': title_keys,
        'watched_title_records': {i: titles.get(i) for i in sorted(watched_titles, key=int)},
        'native_challenger_sponsors': sponsor_values or None,
        'protected_titles': protections, 'npc_nonreligious_titles': npc_titles,
        'actor_other_held_titles': [row for i, row in titles.items() if row['holder']['identity'] == actor_id and i not in political_ids],
        'qualification': {'native_collection': 'ROOT_SUPPLIED_BOUND_SCHEMA' if binding else 'UNKNOWN_SERIALIZATION', 'saved_title_scope_type': title_kind, 'human_completeness': 'UNKNOWN_REQUIRES_ACTUAL_NATIVE_ROSTER_RECEIPT', 'NPC_AI_clergy_gender': 'UNKNOWN_REQUIRES_ACTUAL_NATIVE_PREDICATE_RECEIPT', 'native_law_properties': 'UNKNOWN'},
        'native_business_credit': None,
    }

def title_owned(row, fid):
    if number(row['variables'], 'lyd_c2_owned_head_title') != '1' or typed_var(row['variables'], 'lyd_c2_owner_faith', 'faith') != fid:
        raise ReadError('legitimate religious Title ownership mismatch')

def compare_protection(state, before):
    protected = {row['title_id']: row for row in state['protected_titles']}
    previous = {row['title_id']: row for row in before['protected_titles']}
    if set(protected) != set(previous):
        raise ReadError('political7 protection identities changed')
    for ident, row in previous.items():
        if protected[ident]['entries'] != row['entries'] or protected[ident]['holder'] != row['holder']:
            raise ReadError('protected full Title AST changed: ' + ident)
    for row in before['npc_nonreligious_titles']:
        ident = row['title_id']
        actual = state['titles'].get(ident)
        if actual is None or actual['entries'] != row['entries'] or actual['holder'] != row['holder']:
            raise ReadError('NPC nonreligious full Title AST changed: ' + ident)
    if {r['title_id'] for r in state['npc_nonreligious_titles']} != {r['title_id'] for r in before['npc_nonreligious_titles']}:
        raise ReadError('NPC nonreligious Title set changed')
    allowed_offices = set()
    for snapshot in (state, before):
        legitimate = snapshot['identity']['I3b_result_head_title']
        if legitimate:
            allowed_offices.add(legitimate)
        claim = saved_title_ref(snapshot, 'lyd_c3_claim_title', required=False)
        if claim:
            row = snapshot['titles'].get(claim)
            identity = snapshot['identity']
            if row is None or row['holder']['identity'] != identity['actor_id'] or number(row['variables'], 'lyd_c3_owned_claim_title') != '1' or typed_var(row['variables'], 'lyd_c3_owner_faith', 'faith') != identity['faith_id'] or typed_var(row['variables'], 'lyd_c3_owner_rite', 'rite') != identity['rite_id']:
                raise ReadError('domain exception requires exact current owned claimant office')
            if claim in previous:
                raise ReadError('political Title cannot be a claimed office domain exception')
            allowed_offices.add(claim)
    def stripped_landed(rows):
        if rows is None:
            raise ReadError('actor landed_data missing for full primary/capital protection')
        result = []
        for row in rows:
            if row['key'] == 'domain':
                if not isinstance(row['value'], list):
                    raise ReadError('unqualified actor domain shape')
                result.append({'key': 'domain', 'value': [item for item in row['value'] if not (item['key'] is None and item['value'] in allowed_offices)]})
            else:
                result.append(row)
        return result
    if stripped_landed(state['actor_landed_data']) != stripped_landed(before['actor_landed_data']):
        raise ReadError('actor full landed AST changed outside exact owned office domain rows')

def preserve_other_challengers(state, before, owned_claim):
    for fid, previous in before['faiths'].items():
        if fid not in state['faiths'] or previous['native_challengers']['items'] is None:
            raise ReadError('before/after native collection missing/unqualified')
        for ident in previous['native_challengers']['items']:
            if ident == owned_claim:
                continue
            if ident not in state['titles'] or state['titles'][ident]['entries'] != before['titles'][ident]['entries']:
                raise ReadError('another challenger full Title AST changed: ' + ident)
            old_sponsors, new_sponsors = before['native_challenger_sponsors'], state['native_challenger_sponsors']
            if old_sponsors is not None and (new_sponsors is None or new_sponsors.get(ident) != old_sponsors.get(ident)):
                raise ReadError('another challenger native sponsorship changed')

def assert_graph(state, phase, before=None, expected_serial=None):
    identity = state['identity']
    aid, hid, fid, rid = (identity[k] for k in ('actor_id', 'incumbent_id', 'faith_id', 'rite_id'))
    current, rite = state['faiths'][fid], state['rites'][rid]
    title = state['native_title']
    if not title or current['head_title']['identity'] != title['title_id']:
        raise ReadError('actual native Title does not equal typed I3b result Title')
    if current['main']['identity'] != rid or rite['parent_faith'] != fid or rite['HoR']['identity'] != aid:
        raise ReadError('main Rite/native HoR protection mismatch')
    title_owned(title, fid)
    holder = aid if phase == 'RECOGNIZE' else hid
    if current['HoF']['identity'] != holder or title['holder']['identity'] != holder:
        raise ReadError('native HoF/current Title holder mismatch')
    if aid == hid or state['characters'][hid]['faith_id'] != fid or state['characters'][hid]['rite_id'] != rid:
        raise ReadError('distinct same-Faith/main NPC identity mismatch')
    if number(state['actor_variables'], 'lyd_i3b_result_code') != '1':
        raise ReadError('actual preceding I3b result is not1')
    for row in state['protected_titles']:
        if row['holder']['identity'] != aid:
            raise ReadError('political Title no longer held by actor')
    if before:
        for key in ('actor_id', 'incumbent_id', 'faith_id', 'rite_id', 'I3b_result_head_title'):
            if identity[key] != before['identity'][key]:
                raise ReadError('before/after typed identity changed: ' + key)
        compare_protection(state, before)
        if state['all_faith_mains'] != before['all_faith_mains'] or state['all_rite_parents'] != before['all_rite_parents']:
            raise ReadError('native Faith/Rite membership graph changed')
        if {i: r['HoR'] for i, r in state['rites'].items()} != {i: r['HoR'] for i, r in before['rites'].items()}:
            raise ReadError('native current-Faith Rite HoR graph changed')
    coll = current['native_challengers']
    if coll['items'] is None:
        raise ReadError('native collection serialization unqualified; DISCOVER only')
    claim = saved_title_ref(state, 'lyd_c3_claim_title', required=False)
    if phase in {'REGISTER', 'ROUND_ACTIVE', 'ROUND_READY', 'ROUND_CANCELLED'}:
        if not claim or claim not in coll['items'] or claim == title['title_id']:
            raise ReadError('exact current claim absent from full native collection')
        claim_title = state['titles'][claim]
        if claim_title['holder']['identity'] != aid or number(claim_title['variables'], 'lyd_c3_owned_claim_title') != '1' or typed_var(claim_title['variables'], 'lyd_c3_owner_faith', 'faith') != fid or typed_var(claim_title['variables'], 'lyd_c3_owner_rite', 'rite') != rid:
            raise ReadError('challenger typed owner/holder mismatch')
        if number(state['actor_variables'], 'lyd_c3_claim_registration_result') != '1':
            raise ReadError('registration result is incomplete/negative')
        if state['native_challenger_sponsors'] is None or state['native_challenger_sponsors'].get(claim) != claim:
            raise ReadError('native exact self-sponsor Title projection unqualified/mismatch')
        if before and phase == 'REGISTER':
            old_claim = saved_title_ref(before, 'lyd_c3_claim_title', required=False)
            old_items = before['faiths'][fid]['native_challengers']['items']
            if old_items is None:
                raise ReadError('before registration collection unqualified')
            expected = old_items if old_claim == claim else old_items + [claim]
            if Counter(coll['items']) != Counter(expected):
                raise ReadError('registration changed native collection beyond exact new Title')
            preserve_other_challengers(state, before, old_claim)
    elif phase in {'WITHDRAW', 'RECOGNIZE'}:
        if claim is not None or 'lyd_c3_claim_registration_result' in state['actor_variables']:
            raise ReadError('owned claim metadata remains after withdrawal')
        if before:
            old_claim = saved_title_ref(before, 'lyd_c3_claim_title', required=False)
            if old_claim and any(old_claim in row['native_challengers']['items'] for row in state['faiths'].values()):
                raise ReadError('withdrawn Title still in native collection')
            retired_row = state['watched_title_records'].get(old_claim) if old_claim else None
            if old_claim and old_claim not in state['watched_title_records']:
                raise ReadError('retired Title must be explicitly watched in after projection')
            if retired_row is not None and retired_row['holder']['status'] == 'VALUE':
                raise ReadError('retired owned Title still has a native holder')
            for fid2, row in before['faiths'].items():
                expected = [i for i in row['native_challengers']['items'] if i != old_claim]
                if Counter(state['faiths'][fid2]['native_challengers']['items']) != Counter(expected):
                    raise ReadError('withdrawal changed another native challenger')
            preserve_other_challengers(state, before, old_claim)
    if phase in {'ROUND_ACTIVE', 'ROUND_READY'}:
        av = state['actor_variables']
        if number(av, 'lyd_c3_active') != '1':
            raise ReadError('round is not active')
        serial = number(av, 'lyd_c3_serial')
        if expected_serial is not None and Decimal(serial) != Decimal(str(expected_serial)):
            raise ReadError('round serial mismatch')
        for name, kind, wanted in [('lyd_c3_round_faith', 'faith', fid), ('lyd_c3_round_main', 'rite', rid), ('lyd_c3_round_head', 'char', hid), ('lyd_c3_round_title', state['qualification']['saved_title_scope_type'], title['title_id'])]:
            if typed_var(av, name, kind) != wanted:
                raise ReadError('round captured binding mismatch: ' + name)
        rite_ids = typed_list(state['actor_lists'], 'lyd_c3_rites', 'rite')
        if set(rite_ids) != set(state['rites']):
            raise ReadError('round all-current-Rite collection incomplete')
        for i in rite_ids:
            row, vs = state['rites'][i], state['rites'][i]['variables']
            if typed_var(vs, 'lyd_c3_proposal_owner', 'char') != aid or number(vs, 'lyd_c3_lock_serial') != serial:
                raise ReadError('Rite owner/serial mismatch')
            required = number(vs, 'lyd_c3_delegate_required')
            if required not in {'0', '1'}:
                raise ReadError('unsupported delegate duty')
            if required == '1':
                delegate = typed_var(vs, 'lyd_c3_delegate', 'char')
                if delegate != row['HoR']['identity'] or delegate not in state['characters'] or state['characters'][delegate]['rite_id'] != i:
                    raise ReadError('delegate identity/native HoR mismatch')
                if phase == 'ROUND_READY' and number(vs, 'lyd_c3_delegate_yes') != '1':
                    raise ReadError('required delegate has not consented')
            elif any(row['rite_id'] == i for row in state['characters'].values()):
                raise ReadError('known living follower assigned dormant delegate duty')
        humans = typed_list(state['actor_lists'], 'lyd_c3_players', 'char')
        if aid not in humans:
            raise ReadError('initiating human absent from captured roster')
        for human in humans:
            row = state['characters'][human]
            vs = row['variables']
            if row['faith_id'] != fid or typed_var(vs, 'lyd_c3_affected_owner', 'char') != aid or number(vs, 'lyd_c3_affected_serial') != serial or typed_var(vs, 'lyd_c3_affected_rite', 'rite') != row['rite_id']:
                raise ReadError('captured human owner/serial/Rite mismatch')
            if phase == 'ROUND_READY' and number(vs, 'lyd_c3_player_yes') != '1':
                raise ReadError('captured human has not consented')
        if phase == 'ROUND_READY' and number(av, 'lyd_c3_head_yes') != '1':
            raise ReadError('NPC incumbent has not released office; rejection remains negative')
    if phase == 'ROUND_CANCELLED' and 'lyd_c3_active' in state['actor_variables']:
        raise ReadError('cancelled round still active')
    if phase == 'RECOGNIZE':
        if not before:
            raise ReadError('recognition requires actual saved pre-ready state')
        assert_graph(before, 'ROUND_READY', expected_serial=expected_serial)
        serial = number(state['actor_variables'], 'lyd_c3_serial')
        if serial != number(before['actor_variables'], 'lyd_c3_serial') or (expected_serial is not None and Decimal(serial) != Decimal(str(expected_serial))):
            raise ReadError('recognition historical serial changed/mismatched')
        if 'lyd_c3_active' in state['actor_variables']:
            raise ReadError('recognized round still active')
        if typed_var(current['variables'], 'lyd_c3_recognized_leader', 'char') != aid:
            raise ReadError('recognized leader native/post metadata mismatch')
    if phase in {'ROUND_CANCELLED', 'RECOGNIZE'}:
        for row in state['rites'].values():
            for name in ('lyd_c3_proposal_owner', 'lyd_c3_lock_serial', 'lyd_c3_delegate_required', 'lyd_c3_delegate_yes', 'lyd_c3_delegate'):
                if name in row['variables']:
                    raise ReadError('current round Rite lock/ballot remains after release')
        if before:
            humans = typed_list(before['actor_lists'], 'lyd_c3_players', 'char', required=False) or []
            for human in humans:
                if human not in state['characters']:
                    raise ReadError('released human must remain explicitly watched')
                for name in ('lyd_c3_affected_owner', 'lyd_c3_affected_serial', 'lyd_c3_affected_rite', 'lyd_c3_player_yes'):
                    if name in state['characters'][human]['variables']:
                        raise ReadError('current captured human consent metadata remains after release')
    return {'status': 'SAVED_GRAPH_ASSERTIONS_MATCH', 'phase': phase, 'full_native_challenger_items': coll['items'], 'protection_compared': before is not None, 'native_business_credit': None, 'serialization_semantics_tool_verified': False, 'fresh_runtime_verified': False, 'NPC_AI_choice_receipt_verified': False, 'human_completeness_verified': False}

def assert_repeat_round(before, after):
    previous = Decimal(number(before['actor_variables'], 'lyd_c3_serial'))
    current = Decimal(number(after['actor_variables'], 'lyd_c3_serial'))
    if current != previous + 1:
        raise ReadError('repeat council must use exactly fresh serial+1')
    result = assert_graph(after, 'ROUND_ACTIVE', before, expected_serial=current)
    result['previous_serial'] = str(previous)
    result['new_serial'] = str(current)
    return result

def assert_stale_timeout_preservation(before, after, old_serial):
    if Decimal(number(before['actor_variables'], 'lyd_c3_serial')) <= Decimal(str(old_serial)):
        raise ReadError('old timeout serial is not older than current round')
    assert_graph(before, 'ROUND_ACTIVE')
    assert_graph(after, 'ROUND_ACTIVE', before)
    def current_state(snapshot):
        return {'actor_variables': {k: v for k, v in snapshot['actor_variables'].items() if k.startswith('lyd_c3_')}, 'actor_lists': {k: v for k, v in snapshot['actor_lists'].items() if k.startswith('lyd_c3_')}, 'rites': {k: v['variables'] for k, v in snapshot['rites'].items()}, 'native_title': snapshot['native_title'], 'faith_native_collections': {k: v['native_challengers'] for k, v in snapshot['faiths'].items()}}
    if current_state(before) != current_state(after):
        raise ReadError('old timeout changed current serial/locks/consent/native offices')
    return {'status': 'SAVED_NEW_ROUND_PRESERVED', 'old_serial': str(old_serial), 'actual_old_event_delivery_verified': False, 'native_business_credit': None}

def pinned_ref(ref, maximum):
    if not isinstance(ref, dict) or set(ref) != {'path', 'bytes', 'sha256'} or not isinstance(ref['path'], str) or not Path(ref['path']).is_absolute() or type(ref['bytes']) is not int or not 0 <= ref['bytes'] <= maximum or not isinstance(ref['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', ref['sha256']):
        raise ReadError('fully bound exact file reference required')
    path = Path(ref['path'])
    if not path.is_file() or path.stat().st_size != ref['bytes']:
        raise ReadError('file size differs from bound reference before body read')
    raw = path.read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ReadError('file bytes/SHA mismatch')
    return raw

def main(request_path):
    if request_path.stat().st_size > 128 * 1024:
        raise ReadError('request JSON byte limit exceeded')
    request = strict_json(request_path.read_bytes())
    keys = {'schema', 'source_head', 'phase', 'actor_id', 'incumbent_id', 'political_title_ids', 'save', 'schema_binding', 'before_state', 'expected_serial', 'output'}
    if set(request) != keys or request['schema'] != 'lyd.c3.checkpoint-reader-request.v1' or request['source_head'] != SOURCE_HEAD:
        raise ReadError('closed frozen632 request required')
    phases = {'DISCOVER', 'HANDOFF', 'REGISTER', 'WITHDRAW', 'ROUND_ACTIVE', 'ROUND_READY', 'ROUND_CANCELLED', 'RECOGNIZE'}
    if request['phase'] not in phases or type(request['actor_id']) is not int or type(request['incumbent_id']) is not int:
        raise ReadError('fully bound identities/phase required before opening save')
    identifier(str(request['actor_id']), 'actor')
    identifier(str(request['incumbent_id']), 'incumbent')
    political = request['political_title_ids']
    if not isinstance(political, list) or len(political) != 7 or not all(type(i) is int for i in political) or len(set(political)) != 7:
        raise ReadError('fully bound political7 required before opening save')
    for ident in political:
        identifier(str(ident), 'political Title')
    if not isinstance(request['output'], str) or not Path(request['output']).is_absolute():
        raise ReadError('fully bound external output required before opening save')
    out = Path(request['output']).resolve()
    root = HERE.parent.resolve()
    if out.exists() or out == root or not out.is_relative_to(root):
        raise ReadError('new external result directory required before save read')
    binding = None
    if request['schema_binding'] is not None:
        binding = strict_json(pinned_ref(request['schema_binding'], 1024 * 1024))
        if binding.get('authority') != 'ROOT_ACTUAL_NATIVE_SERIALIZATION_CROSSCHECK' or binding.get('fixture_only') is not False:
            raise ReadError('actual native serialization qualification required; synthetic binding forbidden')
        pinned_ref(binding['qualification_evidence'], 4 * 1024 * 1024)
    if request['phase'] != 'DISCOVER' and binding is None:
        raise ReadError('strict graph requires native serialization binding before save read')
    if request['phase'] != 'DISCOVER' and (not isinstance(binding.get('title_variable_type'), str) or not binding['title_variable_type'] or not isinstance(binding.get('collection'), dict)):
        raise ReadError('strict graph requires qualified Title typename/collection before save read')
    before = strict_json(pinned_ref(request['before_state'], 128 * 1024 * 1024)) if request['before_state'] is not None else None
    raw = pinned_ref(request['save'], MAX_SAVE_BYTES)
    if raw.startswith(b'PK'):
        raise ReadError('compressed save unqualified; preserve and separately qualify decode')
    watched_chars = list(before['characters']) if before else []
    watched_titles = list(before['titles']) if before else []
    state = project(raw.decode('utf-8-sig'), request['actor_id'], request['incumbent_id'], request['political_title_ids'], binding, watched_chars, watched_titles)
    result = {'status': 'DISCOVERY_ONLY_NATIVE_SERIALIZATION_UNKNOWN', 'native_business_credit': None} if request['phase'] == 'DISCOVER' else assert_graph(state, request['phase'], before, request['expected_serial'])
    out.mkdir(parents=True)
    for name, value in [('STATE.json', state), ('REPORT.json', {'schema': 'lyd.c3.checkpoint-reader-report.v1', 'result': result, 'actual_save': request['save'], 'source_head': SOURCE_HEAD, 'request_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest(), 'native_business_credit': None})]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    records = [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())]
    (out / 'INDEX.json').write_text(json.dumps({'files': records}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(out), 'result': result}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    main(parser.parse_args().request)
