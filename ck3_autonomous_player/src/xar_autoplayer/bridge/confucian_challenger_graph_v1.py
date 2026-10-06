"""Complete native Faith challenger registrations and current-holder sponsor scopes."""
from __future__ import annotations

from copy import deepcopy
from .confucian_readonly_private_v1 import (
    _common_payload, exact, full_id, integer, reason,
)

PERMISSION = 'allow_private_confucian_challenger_queries'
SCHEMA = 'ck3_12003_confucian_challenger_graph_v1'
QUALIFICATION = {
    'kind': 'exact_current_static_abi',
    'faith_rtti_index_sha256': '712298a183573a588c24fd0a357e0d83d4e6886a9e5ddd45db7ddf8e5a3aba2d',
    'faith_challenger_abi_index_sha256': '3dffb1d4ee1fa0e100ea26b12f577841317ebdcae4d6e702282bad768ceadfb1',
    'record_layout_index_sha256': '3e24fe49a46749ce353274c2a22659f229802a972b720b6153349effe01af35f',
    'title_properties_index_sha256': '14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a',
    'title_laws_index_sha256': '9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60',
    'runtime_acceptance': None,
}
LAW = 'temporal_head_of_faith_succession_law'
PROPERTY_FIELDS = {'destroy_if_invalid_heir', 'no_automatic_claims',
                   'definitive_form', 'always_follows_primary_heir'}


def validate_faith_ids(value):
    if type(value) is not list or not 1 <= len(value) <= 8:
        raise ValueError('faith_full_ids requires an actual list of 1..8 full Faith IDs')
    for identity in value:
        full_id(identity, 'Faith full identity')
    if len(set(value)) != len(value):
        raise ValueError('Faith selector contains duplicate full identities')
    return list(value)


def _title(value):
    exact(value, {'available', 'unavailable_reason', 'title_absent', 'title_full_id',
        'native_title_class', 'holder_absent', 'holder_character_full_id',
        'holder_current_faith_full_id', 'title_properties', 'title_laws'}, 'graph Title')
    if value['available'] is not True or type(value['title_absent']) is not bool:
        raise ValueError('complete graph requires actual Title presence/availability')
    reason(value['unavailable_reason'], False, 'graph Title')
    props = exact(value['title_properties'], {'available', 'unavailable_reason', *PROPERTY_FIELDS}, 'graph properties')
    laws = exact(value['title_laws'], {'available', 'unavailable_reason', 'native_count',
        'complete_laws', 'expected_law_key', 'expected_law_member'}, 'graph laws')
    if laws['expected_law_key'] != LAW:
        raise ValueError('exact expected Title law differs')
    if value['title_absent']:
        if any(value[key] is not None for key in ('title_full_id', 'native_title_class',
                'holder_absent', 'holder_character_full_id', 'holder_current_faith_full_id')):
            raise ValueError('absent Title cannot invent identity or holder')
        for leaf, fields in ((props, PROPERTY_FIELDS), (laws, {'native_count', 'complete_laws', 'expected_law_member'})):
            if leaf['available'] is not False or any(leaf[key] is not None for key in fields):
                raise ValueError('absent Title requires null leaf data')
            reason(leaf['unavailable_reason'], True, 'absent Title leaf')
        return value
    full_id(value['title_full_id'], 'graph Title full identity')
    if value['native_title_class'] != 'CLandedTitle' or type(value['holder_absent']) is not bool:
        raise ValueError('actual Title class and holder presence required')
    if value['holder_absent']:
        if value['holder_character_full_id'] is not None or value['holder_current_faith_full_id'] is not None:
            raise ValueError('absent holder cannot supply a Character or Faith')
    else:
        full_id(value['holder_character_full_id'], 'holder full identity')
        full_id(value['holder_current_faith_full_id'], 'holder current Faith')
    if props['available'] is not True or any(type(props[key]) is not bool for key in PROPERTY_FIELDS):
        raise ValueError('present Title requires four actual bool properties')
    reason(props['unavailable_reason'], False, 'graph properties')
    rows = laws['complete_laws']
    if (laws['available'] is not True or type(rows) is not list
            or integer(laws['native_count'], 0, 256, 'law count') != len(rows)):
        raise ValueError('present Title requires its complete actual law array/count')
    reason(laws['unavailable_reason'], False, 'graph laws')
    for row in rows:
        exact(row, {'native_definition_id', 'key'}, 'graph law row')
        integer(row['native_definition_id'], 0, 2**32-1, 'native law identity')
        if type(row['key']) is not str or not row['key']:
            raise ValueError('actual native law key required')
    if (type(laws['expected_law_member']) is not bool
            or laws['expected_law_member'] is not any(row['key'] == LAW for row in rows)):
        raise ValueError('expected-law membership differs from complete array')
    return value


def normalize_graph(value, binding, faith_full_ids):
    requested = validate_faith_ids(faith_full_ids)
    exact(value, {'schema', 'game_version', 'executable_sha256', 'read_only', 'available',
        'graph_complete', 'unavailable_reason', 'capture_epoch', 'date_raw', 'played_character_id',
        'played_character_full_id', 'requested_faith_full_ids', 'faiths', 'mod_owned_markers',
        'saved_owner_faith_variables', 'qualification'}, 'complete challenger graph')
    _common_payload(value, SCHEMA, binding)
    if (value['read_only'] is not True or type(value['graph_complete']) is not bool
            or type(value['played_character_full_id']) is not int
            or value['played_character_full_id'] != (binding['played_character_id'] & 0xFFFFFFFF)):
        raise ValueError('actual readonly player/completeness binding required')
    if validate_faith_ids(value['requested_faith_full_ids']) != requested:
        raise ValueError('native graph selectors differ from actual request')
    if value['mod_owned_markers'] is not None or value['saved_owner_faith_variables'] is not None:
        raise ValueError('native registrations do not authenticate saved mod ownership')
    qualification = exact(value['qualification'], QUALIFICATION, 'graph static qualification')
    if any(type(qualification[key]) is not type(wanted) or qualification[key] != wanted
            for key, wanted in QUALIFICATION.items()):
        raise ValueError('graph exact-current static qualification differs')
    if value['graph_complete'] is not value['available']:
        raise ValueError('complete graph availability differs')
    reason(value['unavailable_reason'], not value['available'], 'complete graph')
    if not value['available']:
        if value['faiths'] is not None:
            raise ValueError('unavailable native graph must preserve null collections')
        return deepcopy(value)
    faiths = value['faiths']
    if type(faiths) is not list or len(faiths) != len(requested):
        raise ValueError('complete graph must contain every requested Faith')
    for expected_id, faith in zip(requested, faiths):
        exact(faith, {'requested_faith_full_id', 'available', 'collection_complete',
            'unavailable_reason', 'native_count', 'complete_native_challenger_title_ids', 'challengers'}, 'Faith collection')
        if (full_id(faith['requested_faith_full_id'], 'Faith collection identity') != expected_id
                or faith['available'] is not True or faith['collection_complete'] is not True):
            raise ValueError('Faith collection identity/completeness differs')
        reason(faith['unavailable_reason'], False, 'Faith collection')
        count = integer(faith['native_count'], 0, 4096, 'challenger native count')
        identities, rows = faith['complete_native_challenger_title_ids'], faith['challengers']
        if type(identities) is not list or type(rows) is not list or count != len(identities) or count != len(rows):
            raise ValueError('complete native challenger count and arrays differ')
        for identity in identities:
            full_id(identity, 'challenger full Title identity')
        if len(set(identities)) != len(identities):
            raise ValueError('duplicate native challenger full identities')
        for identity, row in zip(identities, rows):
            exact(row, {'challenger_title_full_id', 'available', 'unavailable_reason', 'challenger_title',
                'registered_sponsor_title', 'scope_sponsor_available', 'scope_lookup_complete',
                'scope_sponsor_unavailable_reason', 'scope_lookup_faith_full_id', 'scope_lookup_native_count',
                'scope_lookup_faith_matches_collection', 'scope_matches_registered_pair', 'scope_sponsor_title'}, 'challenger relation')
            if (full_id(row['challenger_title_full_id'], 'challenger relation identity') != identity
                    or row['available'] is not True or row['scope_sponsor_available'] is not True
                    or row['scope_lookup_complete'] is not True):
                raise ValueError('complete challenger relation required')
            reason(row['unavailable_reason'], False, 'challenger relation')
            reason(row['scope_sponsor_unavailable_reason'], False, 'current-holder sponsor scope')
            challenger = _title(row['challenger_title'])
            registered = _title(row['registered_sponsor_title'])
            scope = _title(row['scope_sponsor_title'])
            if challenger['title_absent'] or challenger['title_full_id'] != identity or challenger['holder_absent']:
                raise ValueError('actual challenger Title/current holder required')
            scope_faith = full_id(row['scope_lookup_faith_full_id'], 'scope current-holder Faith')
            integer(row['scope_lookup_native_count'], 0, 4096, 'scope native count')
            if scope_faith != challenger['holder_current_faith_full_id']:
                raise ValueError('sponsor scope must use challenger holder current Faith')
            if (type(row['scope_lookup_faith_matches_collection']) is not bool
                    or row['scope_lookup_faith_matches_collection'] is not (scope_faith == expected_id)):
                raise ValueError('stored collection vs current-holder Faith fact differs')
            matches = scope['title_full_id'] == registered['title_full_id']
            if type(row['scope_matches_registered_pair']) is not bool or row['scope_matches_registered_pair'] is not matches:
                raise ValueError('actual stored-vs-scope sponsor equality differs')
            if scope_faith == expected_id and (row['scope_lookup_native_count'] != count or not matches):
                raise ValueError('same native Faith lookup must preserve the registered sponsor pair')
    return deepcopy(value)


def project_native_graph_query(raw, binding, faith_full_ids):
    """Project graph envelopes without changing the frozen G2/G3 DTO entrypoints."""
    from .confucian_readonly_private_v1 import CK3_12003, ENVELOPE_KEYS, OPERATIONS
    step, domain, backend, nested, schema = OPERATIONS['challenger_graph']
    exact(raw, ENVELOPE_KEYS | {nested}, 'native Confucian readonly envelope')
    expected = {'step': step, 'accepted': True, 'private_build': True, 'read_only': True,
        'advertised': False, 'game_version': '1.20.0.3', 'domain_key': domain,
        'backend_id': backend, 'snapshot_revision': binding['native_revision'], 'date_raw': binding['date_raw']}
    if any(type(raw[name]) is not type(wanted) or raw[name] != wanted for name, wanted in expected.items()):
        raise ValueError('native Confucian envelope differs from actual operation/frame')
    if type(raw['executable_sha256']) is not str or raw['executable_sha256'].upper() != CK3_12003.executable_sha256:
        raise ValueError('native Confucian envelope image differs')
    value = normalize_graph(raw[nested], binding, faith_full_ids)
    if raw['status'] != ('observed' if value['available'] else 'unavailable'):
        raise ValueError('native Confucian envelope availability differs')
    return {'schema': 'ck3-confucian-readonly-public-v1', 'operation': 'challenger_graph', 'native_result': deepcopy(raw),
        'queried_snapshot_id': binding['snapshot_id'], 'queried_revision': binding['revision'],
        'queried_native_revision': binding['native_revision'], 'date_raw': binding['date_raw'],
        'game_pid': binding['game_pid'], 'connection_generation': binding['connection_generation'],
        'player_character_id': binding['played_character_id'], 'business_postcondition_verified': False,
        'full_product_acceptance_credit': False}


def normalize_public_graph_query(raw, binding, faith_full_ids):
    from .confucian_readonly_private_v1 import PUBLIC_KEYS
    exact(raw, PUBLIC_KEYS, 'public Confucian readonly result')
    projected = project_native_graph_query(raw['native_result'], binding, faith_full_ids)
    if any(type(raw[name]) is not type(wanted) or raw[name] != wanted for name, wanted in projected.items()):
        raise ValueError('public Confucian read binding or credit changed')
    return deepcopy(raw)


def query_confucian_challenger_graph_private_v1(driver, faith_full_ids, *, expected_revision, timeout_seconds=10.0):
    from .confucian_readonly_private_v1 import query_confucian_readonly_private_v1
    return query_confucian_readonly_private_v1(driver, 'challenger_graph', expected_revision=expected_revision,
        faith_full_ids=faith_full_ids, timeout_seconds=timeout_seconds)
