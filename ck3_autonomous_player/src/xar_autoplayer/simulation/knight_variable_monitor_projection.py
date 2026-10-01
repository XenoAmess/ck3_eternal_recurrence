"""Pure projection of the two-character native variable/house monitor.

The caller must separately bind the original receipt, PID/connection/source and
begin/finish lifecycle. This module never calls native helpers or fills symbolic
values from a saved endpoint. A missing event producer remains a specific gap.
"""
from __future__ import annotations

NOTIFICATION_KEYS = {f'death_management.{n}' for n in (1200, 1201, 1202, 1204, 1205, 1206, 1207)}


def _prearmed_producers(monitor: dict) -> dict[str, dict] | None:
    if monitor.get('event_producer_definitions_read') is not True:
        return None
    if monitor.get('notification_receiver_inferred_as_victim') is not False:
        raise ValueError('notification receiver must not be inferred as victim')
    count = monitor['event_definition_count']
    if type(count) is not int or not (7 <= count <= 1_048_576) or monitor['event_manager_token'] <= 0:
        raise ValueError('invalid initialized event definition registry tuple')
    definitions = monitor['prearmed_event_definitions']
    keys = [p['definition_key'] for p in definitions]
    if len(keys) != 7 or set(keys) != NOTIFICATION_KEYS:
        raise ValueError('seven unique source-bound notification definitions required')
    for field in ('definition_token', 'compiled_immediate_root_token', 'definition_index'):
        if len({p[field] for p in definitions}) != 7:
            raise ValueError('ambiguous notification definition/root identity')
    for p in definitions:
        if not (p['identity_read'] is True and p['actual_original_execution_observed'] is False and
                p['invocation'] == 0 and p['definition_token'] > 0 and p['compiled_immediate_root_token'] > 0 and
                0 <= p['definition_index'] < count and p['definition_vtable_rva'] == 0x42F5710 and
                p['root_vtable_rva'] == 0x44CF030 and p['original_execute_rva'] == 0x3380EC0 and
                type(p['definition_id']) is int and 0 <= p['definition_id'] < 2**32 and
                type(p['runtime_stats_ordinal']) is int and 0 <= p['runtime_stats_ordinal'] < 2**32 and
                type(p['root_hash']) is int and 0 <= p['root_hash'] < 2**32):
            raise ValueError('notification prearm identity is not a valid original definition/root binding')
    return {p['definition_key']: p for p in definitions}


def _actual_producer(enter: dict, returned: dict, bindings: dict[str, dict] | None) -> dict | None:
    p, q = enter.get('event_producer'), returned.get('event_producer')
    if not p or p.get('identity_read') is not True:
        if q and q.get('identity_read') is True:
            raise ValueError('producer appears only after original setter returned')
        return None
    if p != q:
        raise ValueError('producer lifecycle identity changed within original setter invocation')
    if bindings is None:
        raise ValueError('actual producer without original prearm definitions')
    bound = bindings.get(p['definition_key'])
    fields = ('definition_token', 'definition_index', 'definition_id', 'runtime_stats_ordinal',
              'definition_key', 'compiled_immediate_root_token', 'definition_vtable_rva',
              'root_vtable_rva', 'root_hash', 'original_execute_rva')
    if bound is None or any(p[k] != bound[k] for k in fields):
        raise ValueError('actual notification root does not match prearmed definition')
    if not (p['actual_original_execution_observed'] is True and type(p['invocation']) is int and
            p['invocation'] > 0 and p['execution_context_token'] > 0 and p['root_scope_token'] > 0 and
            p.get('identity_kind') == 'nearest_matched_notification_immediate_ancestor' and
            type(p.get('matched_root_execution_depth')) is int and p['matched_root_execution_depth'] > 0 and
            type(p.get('active_effect_group_depth')) is int and
            p['active_effect_group_depth'] >= p['matched_root_execution_depth'] and
            len(p['root_scope_words']) == 2 and all(type(w) is int for w in p['root_scope_words'])):
        raise ValueError('actual original notification execution/context missing')
    # The root receiver may be a third character. Never substitute the setter's
    # character for this original scope or infer named dead_character from it.
    return dict(p)


def _flag(value: dict, monitor: dict, *, required: bool) -> dict | None:
    if value.get('read') is not True or value.get('present') is not True:
        if required:
            raise ValueError('actual requested/written value was not independently read')
        return None
    word0, word1 = value['scope_word0'], value['scope_word1']
    if type(word0) is not int or type(word1) is not int or word0 & 0xFFFF != 3:
        raise ValueError('signature value must be an original typed flag')
    index = word1 & 0xFFFFFF
    if value['flag_name_read'] is not True or value['flag_index'] != index or not value['flag_name']:
        raise ValueError('requested flag lacks matching native identifier name/index')
    if value['flag_identifier_epoch'] != monitor['native_identifier_epoch'] or not (
        0 <= index < value['flag_identifier_count'] and
        monitor['native_identifier_count'] <= value['flag_identifier_count'] <= 1_048_576
    ):
        raise ValueError('requested flag identifier epoch/count/index invalid')
    return {'raw_words': [word0, word1], 'flag_index': index,
            'identifier_epoch': value['flag_identifier_epoch'],
            'identifier_count': value['flag_identifier_count'], 'native_name': value['flag_name']}


def validate_owner_return_compression(monitor: dict) -> dict | None:
    """Validate additive native compression metadata without inventing call order.

    Old native originals omit this additive field. Null means no value was read,
    never a known absent signature. Aggregate first/last are bounds only.
    """
    compression = monitor.get('owner_return_compression')
    if compression is None:
        return None

    def require(passed: bool, message: str):
        if not passed:
            raise ValueError('owner return compression: ' + message)

    require(type(compression) is dict and type(compression.get('schema_version')) is int and compression['schema_version'] == 1 and
            compression.get('scope') == 'exact_dead_null_original_returns_only', 'native schema/scope')
    fields = ('observed', 'retained', 'coalesced', 'unchanged_nonnull_unrecorded')
    require(all(type(compression.get(key)) is int and 0 <= compression[key] < 2**64
                for key in fields), 'actual count types/range')
    require(type(compression.get('capacity')) is int and compression['capacity'] == 128 and
            type(compression.get('writer_calls_coalesced')) is int and
            compression['writer_calls_coalesced'] == 0 and
            compression.get('aggregate_bounds_are_not_per_call_chronology') is True,
            'original capacity/writer/chronology boundary')
    records = monitor['records']
    owner_rows = [r for r in records if r['boundary'] == 'original_owner_return']
    require(compression['retained'] == len(owner_rows), 'retained original getter rows')
    multiplicity = 0
    first_indices = []
    for row in records:
        count = row.get('owner_observation_count')
        require(type(count) is int and 0 <= count < 2**64, 'row multiplicity type')
        if row['boundary'] != 'original_owner_return':
            require(count == 0, 'non-getter operation must not be compressed')
            continue
        first, last = row.get('owner_observation_first_call_index'), row.get('owner_observation_last_call_index')
        require(type(first) is int and type(last) is int and
                0 <= first <= last < compression['observed'] and
                1 <= count <= last - first + 1 and (count != 1 or first == last),
                'original observed call index bounds')
        require(type(row.get('owner_state_epoch')) is int and row['owner_state_epoch'] > 0 and
                type(row.get('owner_activity_epoch')) is int and row['owner_activity_epoch'] >= 0,
                'state/activity epoch types')
        first_indices.append(first)
        multiplicity += count
        if count > 1:
            words = row['native_scope_words']
            require(row['failure_flags'] == 0 and row['dead'] is True and
                    row['full_identity_matches'] is True and
                    row['owner_from_original_getter'] is True and
                    row['owner_token'] == 0 and row['container_token'] == 0 and
                    row['value']['read'] is False and row['character_id'] == row['observed_character_id'] and
                    row['character_id'] in monitor['character_ids'] and
                    row['key_id'] == monitor['signature_weapon_key_id'] and
                    type(row['thread_id']) is int and row['thread_id'] > 0 and
                    row['native_root_scope_token'] > 0 and row['caller_token'] > 0 and
                    len(words) == 2 and all(type(word) is int for word in words) and
                    words[0] & 0xFFFF == 4 and words[1] == row['character_id'],
                    'only source-bound full-ID dead/null getter returns aggregate')
    require(first_indices == sorted(set(first_indices)), 'unique retained first call indices')
    require(compression['coalesced'] == multiplicity - compression['retained'], 'coalesced original calls')
    require(compression['observed'] == multiplicity + compression['unchanged_nonnull_unrecorded'],
            'observed calls exhaustively accounted for')
    return dict(compression)


def validate_variable_monitor(monitor: dict | None, *, character_ids: list[int],
                              expected_monitor_token: int, before_date_raw: int,
                              after_date_raw: int, expected_thread: int | None = None) -> dict:
    """Check the original monitor tuple and project actual writes/guard returns.

    The monitor token is independent of the managed-daily token. ``expected_thread``
    binds the controlled arm/final lifecycle, not GUI callbacks. Each original
    operation must retain its own thread/context. Native owner final rows do not
    dereference a cached pointer; saved endpoints and original-owner observations
    remain separate evidence.
"""
    if monitor is None:
        return {'status': 'NOT_CAPTURED', 'actual_write_pairs': [],
                'producer_closed': False, 'gaps': ['independent scoped_variable_monitor absent'],
                'whole_game_mutable_bundle_complete': False}
    checks = []

    def check(name: str, passed: bool):
        checks.append({'name': name, 'pass': bool(passed)})
        if not passed:
            raise ValueError('variable monitor: ' + name)

    check('schema1', monitor['schema_version'] == 1)
    check('two exact full characters', monitor['character_ids'] == character_ids and
          len(character_ids) == 2 and len(set(character_ids)) == 2)
    check('actual monitor token', type(expected_monitor_token) is int and expected_monitor_token > 0 and
          monitor['monitor_sequence_token'] == expected_monitor_token)
    check('begin paused date', monitor['begin_date_raw'] == before_date_raw)
    check('zero or one native day window', after_date_raw - before_date_raw in (0, 24))
    check('no truncation/failure', monitor['truncated'] is False and monitor['failure_flags'] == 0)
    check('real uninstall receipt flag', monitor['detours_uninstalled'] is True)
    check('global and endpoint-cause flags retained', monitor['whole_game_mutable_bundle_complete'] is False and
          monitor['battle_event_causality_inferred_from_endpoint'] is False and
          monitor['final_owner_state_reread_from_cached_pointer'] is False)
    epoch, count, key_id = (monitor[k] for k in ('native_identifier_epoch', 'native_identifier_count', 'signature_weapon_key_id'))
    check('independent signature key epoch/index', 0 <= epoch <= 127 and 0 < count <= 1_048_576 and
          monitor['native_identifier_table_token'] > 0 and key_id > 0 and
          key_id >> 24 == epoch and key_id & 0xFFFFFF < count)
    records = monitor['records']
    owner_compression = validate_owner_return_compression(monitor)
    producer_bindings = _prearmed_producers(monitor)
    check('nonempty arm through final paused', bool(records) and records[0]['boundary'] == 'arm' and
          records[-1]['boundary'] == 'final_paused' and records[0]['date_raw'] == before_date_raw and
          records[-1]['date_raw'] == after_date_raw)
    check('unique ordered original sequences', [r['sequence'] for r in records] == sorted({r['sequence'] for r in records}))
    check('every record same declared window', all(r['failure_flags'] == 0 and r['date_raw'] in
          (before_date_raw, after_date_raw) and r['key_id'] == key_id and
          type(r['thread_id']) is int and 0 < r['thread_id'] < 2**32 for r in records))
    lifecycle_thread = records[0]['thread_id']
    check('controlled arm/final lifecycle thread',
          (expected_thread is None or lifecycle_thread == expected_thread) and
          all(r['thread_id'] == lifecycle_thread for r in records if r['boundary'] in ('arm', 'final_paused')))
    check('every scoped character full identity', all(r['character_id'] == -1 or
          (r['character_id'] in character_ids and r['observed_character_id'] == r['character_id'] and
           r['full_identity_matches'] is True) for r in records))
    pairs = {}
    for row in records:
        if row['boundary'] in ('variable_write_enter', 'variable_write_return', 'house_predicate_enter', 'house_predicate_return'):
            kind, edge = row['boundary'].rsplit('_', 1)
            check('positive actual invocation', type(row['invocation']) is int and row['invocation'] > 0)
            pair = pairs.setdefault((kind, row['invocation']), {})
            check('no duplicate actual invocation edge', edge not in pair)
            pair[edge] = row
    check('complete ordered paired original calls', all(set(p) == {'enter', 'return'} and
          p['enter']['sequence'] < p['return']['sequence'] and p['enter']['thread_id'] == p['return']['thread_id']
          for p in pairs.values()))
    operation_binding = ('key_id', 'character_id', 'observed_character_id', 'full_identity_matches',
                         'execution_context_token', 'native_root_scope_token', 'native_scope_words',
                         'setter_node_token', 'setter_node_vtable_rva', 'setter_node_hash',
                         'daily_effect_context', 'current_death_commit_context', 'event_producer')
    check('each original operation preserves context/key/full identity', all(
          all(pair['enter'].get(field) == pair['return'].get(field) for field in operation_binding)
          for pair in pairs.values()))
    writes, houses = [], []
    for (kind, invocation), pair in pairs.items():
        enter, returned = pair['enter'], pair['return']
        if kind == 'variable_write':
            fixed = ('character_id', 'owner_token', 'container_token', 'key_id',
                     'setter_node_token', 'setter_node_vtable_rva', 'setter_node_hash', 'execution_context_token',
                     'native_root_scope_token', 'native_scope_words')
            check('write original request/node/context stable', all(enter[k] == returned[k] for k in fixed))
            check('write current actual owner and container', enter['character_id'] in character_ids and
                  enter['owner_token'] > 0 and enter['container_token'] == enter['owner_token'] + 8 and
                  all(r['owner_from_original_getter'] is True and r['owner_from_same_setter_invocation'] is True
                      for r in (enter, returned)))
            check('write actual original node/context retained', enter['setter_node_token'] > 0 and
                  enter['setter_node_vtable_rva'] == 0x44D19B0 and enter['execution_context_token'] > 0 and
                  enter['native_root_scope_token'] > 0)
            check('setter context actual full character scope', len(enter['native_scope_words']) == 2 and
                  enter['native_scope_words'][0] & 0xFFFF == 4 and
                  enter['native_scope_words'][1] == enter['character_id'])
            requested = _flag(enter['requested_value_decoding'], monitor, required=True)
            # Request arguments are captured at original entry only. Return DTO
            # request fields are deliberately unread defaults; never turn them
            # into a second observation or require invented repeated values.
            check('request decode from original typed words', requested['raw_words'] == enter['requested_scope_words'])
            written = _flag(returned['value'], monitor, required=True)
            check('original setter returned matching written words/name', written['raw_words'] == requested['raw_words'] and
                  written['native_name'] == requested['native_name'])
            before = _flag(enter['value'], monitor, required=False)
            check('before row actually read even when absent', enter['value']['read'] is True)
            writes.append({'invocation': invocation, 'character_id': enter['character_id'],
                           'sequence_enter': enter['sequence'], 'sequence_return': returned['sequence'],
                           'date_raw': enter['date_raw'], 'owner_token': enter['owner_token'],
                           'container_token': enter['container_token'], 'key_id': key_id,
                           'requested_flag': requested, 'before_flag': before, 'after_flag': written,
                           'duration': enter['duration'], 'expiration_raw': returned['value']['expiration_raw'],
                           'setter_node_token': enter['setter_node_token'],
                           'setter_node_hash': enter['setter_node_hash'],
                           'execution_context_token': enter['execution_context_token'],
                           'native_scope_words': enter['native_scope_words'],
                           'producer': _actual_producer(enter, returned, producer_bindings),
                           'time_resolution': 'actual-write-and-operation-before-after'})
        else:
            fixed = ('house_ids', 'relation_type_token', 'relation_type_id', 'relation_type_key', 'caller_token')
            check('house original arguments stable', all(enter[k] == returned[k] for k in fixed))
            check('house original AL returned once', returned['original_boolean_read'] is True and
                  returned['original_boolean'] == bool(returned['original_return_bits'] & 0xFF))
            houses.append({'invocation': invocation, 'house_ids': enter['house_ids'],
                           'relation_type_id': enter['relation_type_id'], 'relation_type_key': enter['relation_type_key'],
                           'original_boolean': returned['original_boolean'],
                           'original_return_bits': returned['original_return_bits'],
                           'sequence_enter': enter['sequence'], 'sequence_return': returned['sequence'],
                           'time_resolution': 'original-predicate-enter-return',
                           'predicate_failure_reason': 'UNKNOWN_UNLESS_ACTUAL_CHILD_PREDICATE_OR_SAME_RUN_CONDITIONS_SUPPLIED'})
    producer_closed = bool(writes) and all(row['producer'] is not None for row in writes)
    gaps = []
    if producer_bindings is None:
        gaps.append('prearmed stable notification definitions/root identities not captured')
    if not writes:
        gaps.append('no matched signature writes observed; a no-write branch requires separate actual branch/inventory proof')
    elif not producer_closed:
        gaps.append('one or more actual signature writes has no matched original notification immediate producer')
    first_owners = []
    for character_id in character_ids:
        owners = [row for row in records if row['boundary'] == 'original_owner_return' and
                  row['character_id'] == character_id]
        observation = {'character_id': character_id, 'status': 'UNKNOWN_NO_ORIGINAL_GETTER',
                       'is_arm_initial_state': False, 'is_final_state': False}
        if owners:
            row = owners[0]
            check('first original getter actual owner and typed presence',
                  row['owner_token'] > 0 and row['container_token'] == row['owner_token'] + 8 and
                  row['owner_from_original_getter'] is True and type(row['value']['present']) is bool)
            observation.update({'sequence': row['sequence'], 'thread_id': row['thread_id'],
                                'date_raw': row['date_raw'], 'owner_token': row['owner_token'],
                                'full_identity_matches': row['full_identity_matches']})
            if row['value']['read'] is True:
                flag = _flag(row['value'], monitor, required=False)
                observation.update({'status': 'OBSERVED_PRESENT_AT_ORIGINAL_GETTER' if flag is not None
                                    else 'OBSERVED_ABSENT_AT_ORIGINAL_GETTER', 'flag': flag})
            else:
                observation['status'] = 'UNKNOWN_ORIGINAL_GETTER_VALUE_NOT_READ'
        first_owners.append(observation)
    return {'status': 'CAPTURED_ACTUAL_MONITOR_OPERATIONS_CHECKED', 'checks': checks,
            'monitor_sequence_token': expected_monitor_token, 'actual_write_pairs': writes,
            'original_house_predicate_pairs': houses, 'producer_closed': producer_closed,
            'controlled_lifecycle_thread_id': lifecycle_thread,
            'actual_observer_thread_ids': sorted({r['thread_id'] for r in records}),
            'first_original_owner_observations': first_owners,
            'original_owner_return_compression': owner_compression,
            'prearmed_event_definition_bindings': producer_bindings, 'gaps': gaps,
            'whole_game_mutable_bundle_complete': False,
            'limits': 'Requested names are independently decoded from original typed words. Saved endpoints, UI timing and producer proof are separate checks.'}
