"""Semantic checks for42b's actual due wire, after59d's exact owned _typed.

Raw entry and actual returned values remain separate. Missing reads stay null;
an empty captured vector never supplies its unavailable or negative count.
This module observes no game, reconstructs no current query, and mutates no DTO.
"""
from __future__ import annotations

_SHA = '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'
_RETURN = 0x2A9A67D
_REF_BASIS = 'immutable_entry_source_reference_and_returned_physical_reread'
_REGI_MAGIC = 0x52656769
_COMBAT_MAGIC = 0x436F6D62
_INVALID = 0xFFFFFFFF
_U64_MAX = (1 << 64) - 1
_LOCATIONS = {
    'queue_count_load': 0x2A9AF30,
    'queue_fullid_load': 0x2A9AF95,
    'due_date_compare': 0x2A9B0C8,
    'chunk_bind_call': 0x2A9B15E,
    'army_refresh_call': 0x2A9B502,
}


def _require(passed: bool, name: str) -> None:
    if not passed:
        raise ValueError(f'gathering due {name}')


def _present(value: dict, fields: tuple[str, ...], name: str) -> None:
    _require(all(value[key] is not None for key in fields),
             f'{name} complete declared read has an unavailable field')


def _sequence(count: int | None, rows: list, complete: bool, name: str) -> None:
    if count is None:
        _require(not complete and not rows, f'{name} unavailable count was inferred')
    elif count <= 0:
        _require(complete and not rows, f'{name} signed no-work count/extent differs')
    else:
        _require(len(rows) <= count, f'{name} captured extent exceeds signed count')
        _require(not complete or len(rows) == count,
                 f'{name} complete extent loses native occurrences')


def _list(value: dict, name: str, declared_complete: bool) -> None:
    _sequence(value['count'], value['ordered_full_ids'], value['complete'], name)
    if value['ordered_full_ids'] or (value['complete'] and (value['count'] or 0) > 0):
        _require(value['buffer_identity'] not in (None, 0),
                 f'{name} positive physical extent has no buffer')
    if declared_complete:
        _present(value, ('buffer_identity', 'capacity', 'count'), name)
        _require(value['complete'], f'{name} incomplete extent contradicts all declared reads')
    # Capacity/count are independent signed header reads. In particular a
    # negative count is retained verbatim, regardless of empty payload length.


def _physical(value: dict, name: str, declared_complete: bool = False) -> None:
    selected = value['selected_full_id']
    _require(value['resolution_complete'] == (selected is not None),
             f'{name} selected generation availability differs')
    if value['physical_identity'] == 0:
        _require(selected is None and value['magic'] is None and
                 not value['resolution_complete'] and not value['used_native_fallback'],
                 f'{name} null receiver manufactures resolved fields')
    if declared_complete:
        _require(value['physical_identity'] != 0,
                 f'{name} complete registry reads cannot lose the receiver')
        _present(value, ('selected_full_id', 'magic'), name)
    # A native fallback is a distinct observed physical receiver. Neither its
    # fullID nor its magic is replaced with the requested ID or guessed type.
    # Even a nonfallback selection rereads receiver.full_id after checking its
    # candidate generation. Those separate physical reads may differ.


def _chunk(value: dict, receiver: dict, ordinal: int, name: str,
           declared_complete: bool) -> None:
    address = receiver['physical_identity'] + 0x18 + 36 * ordinal
    expected = address if 0 <= address <= _U64_MAX else 0
    _require(value['ordinal'] == ordinal and value['physical_identity'] == expected,
             f'{name} computed physical chunk/ordinal differs')
    fields = ('maximum', 'current', 'owner_full_id', 'stored_ordinal',
              'association_full_id', 'byte14', 'state', 'date_raw64')
    if expected == 0:
        _require(all(value[key] is None for key in fields),
                 f'{name} unavailable chunk manufactures physical fields')
    if declared_complete:
        _present(value, fields, name)
    # Read raw ownership, stored ordinal, cache, state and full64-bit date as
    # independent fields. They are not repaired from the source reference.


def _ref(value: dict, name: str, declared_complete: bool,
         immutable_input: bool = False) -> None:
    _require(value['source_ref_identity'] != 0,
             f'{name} immutable source reference has no physical entry token')
    receiver = value['receiver']
    _physical(receiver, name + '.receiver',
              declared_complete and (not immutable_input or value['owner_full_id'] is not None))
    if value['owner_full_id'] is None:
        _require(receiver['requested_full_id'] == 0 and receiver['physical_identity'] == 0,
                 f'{name} absent immutable owner manufactures a resolver input')
    else:
        _require(receiver['requested_full_id'] == value['owner_full_id'],
                 f'{name} immutable full owner differs from resolver input')
    can_read_chunk = (value['ordinal'] is not None and receiver['resolution_complete'] and
                      receiver['magic'] == _REGI_MAGIC and
                      receiver['selected_full_id'] != _INVALID)
    _require((value['chunk'] is not None) == can_read_chunk,
             f'{name} source-admitted chunk availability differs')
    if value['chunk'] is not None:
        _chunk(value['chunk'], receiver, value['ordinal'], name + '.chunk', declared_complete)
    if declared_complete and not immutable_input:
        _present(value, ('owner_full_id', 'ordinal'), name)
    # Returned rereads copy these inputs from entry instead of rereading freed
    # reference storage. A missing entry owner/ordinal remains missing even if
    # every physical read actually attempted at return succeeds.


def _record(value: dict, name: str, declared_complete: bool) -> None:
    _require(value['physical_identity'] != 0, f'{name} native record has no physical pointer')
    _sequence(value['pending_count'], value['pending_refs'], value['pending_refs_complete'],
              name + '.pending')
    _sequence(value['character_count'], value['character_full_ids'],
              value['character_ids_complete'], name + '.characters')
    for i, ref in enumerate(value['pending_refs']):
        _require(ref['source_ref_identity'] == value['pending_refs'][0]['source_ref_identity'] + 16 * i,
                 f'{name} pending reference physical stride/order differs')
        _ref(ref, f'{name}.pending[{i}]', declared_complete)
    if declared_complete:
        _present(value, ('date_low32', 'pending_count', 'character_count'), name)
        _require(value['pending_refs_complete'] and value['character_ids_complete'],
                 f'{name} nested partial extent contradicts declared reads')


def _army(value: dict, name: str, declared_complete: bool) -> None:
    _physical(value['receiver'], name + '.receiver', declared_complete)
    _physical(value['combat_receiver'], name + '.combat_receiver', declared_complete)
    combat = value['combat_receiver']
    expected_skip = (combat['magic'] == _COMBAT_MAGIC and
                     combat['selected_full_id'] != _INVALID)
    skip = expected_skip if combat['magic'] is not None and combat['selected_full_id'] is not None else None
    _require(value['source_combat_skip'] is skip,
             f'{name} source combat skip was guessed from combat ID alone')
    if value['combat128'] is not None:
        _require(combat['requested_full_id'] == value['combat128'],
                 f'{name} combat resolver request differs')
    else:
        _require(combat['physical_identity'] == 0 and combat['requested_full_id'] == 0,
                 f'{name} unavailable combat input supplies a receiver')
    _list(value['arrg_roster'], name + '.arrg_roster', declared_complete)
    ids = value['arrg_roster']['ordered_full_ids']
    _require(len(value['arrg']) == len(ids), f'{name} ArRg occurrence copy/order differs')
    for i, (arrg, raw) in enumerate(zip(value['arrg'], ids)):
        at = f'{name}.arrg[{i}]'
        _require(arrg['receiver']['requested_full_id'] == raw,
                 f'{at} requested full generation/order differs')
        _physical(arrg['receiver'], at + '.receiver', declared_complete)
        _sequence(arrg['source_ref_count'], arrg['source_refs'],
                  arrg['source_refs_complete'], at + '.source_refs')
        if arrg['source_refs']:
            _require(arrg['source_refs_identity'] not in (None, 0),
                     f'{at} reference extent has no physical buffer')
        for j, ref in enumerate(arrg['source_refs']):
            _require(ref['source_ref_identity'] == arrg['source_refs_identity'] + 16 * j,
                     f'{at} source reference physical stride/order differs')
            _ref(ref, f'{at}.source_refs[{j}]', declared_complete)
        if declared_complete and arrg['receiver']['physical_identity']:
            _present(arrg, ('current38', 'maximum3c', 'army140', 'owner144',
                            'character148', 'state14c', 'source_refs_identity', 'source_ref_count'), at)
            _require(arrg['source_refs_complete'], f'{at} incomplete declared references')
    _sequence(value['gathering_count'], value['gathering_records'],
              value['gathering_records_complete'], name + '.gathering')
    if value['gathering_count'] is not None and value['gathering_count'] > 0:
        _require(value['gathering_records_complete'] or
                 len(value['gathering_records']) < value['gathering_count'],
                 f'{name} incomplete gathering extent lost no pointer occurrence')
        if declared_complete:
            _require(value['gathering_buffer_identity'] not in (None, 0),
                     f'{name} successful positive gathering count has no physical buffer')
    if value['gathering_records']:
        _require(value['gathering_buffer_identity'] not in (None, 0),
                 f'{name} gathering extent has no physical buffer')
    for i, record in enumerate(value['gathering_records']):
        _record(record, f'{name}.gathering[{i}]', declared_complete)
    raw_statistics = value['statistics130_hex']
    if raw_statistics is not None:
        _require(len(raw_statistics) == 160 and
                 all(c in '0123456789abcdef' for c in raw_statistics),
                 f'{name} exact80-byte raw statistics differs')
    if declared_complete and value['receiver']['physical_identity']:
        _present(value, ('unit124', 'combat128', 'gathering_count',
                         'gathering_buffer_identity', 'finished_date190', 'statistics130_hex'), name)
        # A successfully read null gathering record slot is omitted and marks
        # this extent incomplete without adding a failed declared read. Preserve
        # that distinction from an unavailable count/buffer or failed read.


def _snapshot(value: dict, name: str, captured: bool) -> None:
    declared = value['all_declared_reads_complete']
    _require(not declared or not value['missing_fields'],
             f'{name} complete declared reads retain failures')
    if captured:
        _require(declared == (not value['missing_fields']),
                 f'{name} completed capture/read availability differs')
    _require(value['returned_ref_fields_basis'] == _REF_BASIS,
             f'{name} immutable entry reference basis differs')
    for key in ('queue158', 'persistent_roster30', 'army_roster50'):
        _list(value[key], name + '.' + key, declared)
    for key, roster in (('queued_armies', 'queue158'), ('roster_armies', 'army_roster50')):
        rows = value[key]
        ids = value[roster]['ordered_full_ids']
        _require(len(rows) <= len(ids) and (not captured or len(rows) == len(ids)),
                 f'{name}.{key} physical occurrence extent differs')
        for i, (row, raw) in enumerate(zip(rows, ids)):
            _require(row['receiver']['requested_full_id'] == raw,
                     f'{name}.{key}[{i}] requested full generation/order differs')
            _army(row, f'{name}.{key}[{i}]', declared)
    ids = value['persistent_roster30']['ordered_full_ids']
    rows = value['persistent']
    _require(len(rows) <= len(ids) and (not captured or len(rows) == len(ids)),
             f'{name} persistent occurrence extent differs')
    for i, (row, raw) in enumerate(zip(rows, ids)):
        at = f'{name}.persistent[{i}]'
        _require(row['receiver']['requested_full_id'] == raw,
                 f'{at} requested full generation/order differs')
        _physical(row['receiver'], at + '.receiver', declared)
        physical = row['receiver']['physical_identity']
        _require(len(row['chunks']) == (7 if physical else 0),
                 f'{at} seven physical chunk copies differ')
        for j, chunk in enumerate(row['chunks']):
            _chunk(chunk, row['receiver'], j, f'{at}.chunks[{j}]', declared)
        if declared and physical:
            _present(row, ('prepared148',), at)
    for i, ref in enumerate(value['entry_due_refs_at_return']):
        _ref(ref, f'{name}.entry_due_refs_at_return[{i}]', declared, immutable_input=True)
    if declared:
        _present(value, ('passed_date_raw64', 'game_state_date_raw64',
                         'absolute_day_raw', 'current_c0_raw'), name)
        _require(value['primary_identity'] != 0 and value['date_pointer_identity'] != 0,
                 f'{name} completed read has no physical argument')


def _ordered(parent: dict, entry: dict, returned: dict) -> bool | None:
    tokens = (parent, entry, returned)
    if any(token['clock_identity'] == 0 or token['thread_id'] is None for token in tokens):
        return None
    return (parent['clock_identity'] == entry['clock_identity'] == returned['clock_identity'] and
            parent['thread_id'] == entry['thread_id'] == returned['thread_id'] and
            parent['sequence'] < entry['sequence'] < returned['sequence'])


def _parent_roster(parent: dict, name: str) -> None:
    roster = parent['original_army_roster']
    _require(roster['boundary'] == 'parent_entry' and
             roster['capture_rva'] == parent['actual_entry_rva'] and
             roster['capture_event'] == parent['entry_event'],
             f'{name} copied original roster has no actual postdate entry token')
    count, ids = roster['count'], roster['ordered_full_ids']
    if roster['complete']:
        begin = roster['begin_identity']
        _require(count is not None and count >= 0 and len(ids) == count and
                 begin is not None and roster['end_identity'] == begin + count * 4 and
                 (count == 0 or begin != 0),
                 f'{name} complete original roster extent/order differs')
    else:
        _require(not ids, f'{name} incomplete original roster invents full occurrence copy')


def _event(value: dict, full: int, name: str) -> None:
    parent, entry, returned = value['parent'], value['entry'], value['returned']
    _require(value['actual_boundary_admitted'],
             f'{name} unadmitted independent call cannot own historical Army snapshots')
    _require(value['original_called'] and value['original_returned'],
             f'{name} retained journal has no called and returned original')
    _require(not value['observed'] or value['actual_boundary_admitted'],
             f'{name} entry observation has no actual boundary')
    _require(not value['actual_poststage_observed'] or
             (value['actual_boundary_admitted'] and value['original_called'] and value['original_returned']),
             f'{name} actual poststage has no returned original')
    if value['actual_boundary_admitted']:
        _require(value['actual_return_rva'] == _RETURN and parent['observed'] and
                 parent['phase'] == 'post_date' and parent['actual_entry_rva'] == 0x2A9A570 and
                 parent['primary_manager_identity'] > 0 and
                 parent['secondary_manager_identity'] == parent['primary_manager_identity'] + 8 and
                 0 < parent['game_state_identity'] <= _U64_MAX - 8,
                 f'{name} full actual postdate parent/67D boundary differs')
        _require(entry['primary_identity'] == parent['primary_manager_identity'] and
                 entry['date_pointer_identity'] == parent['game_state_identity'] + 8,
                 f'{name} entry receiver/date argument differs from actual parent')
        _parent_roster(parent, name + '.parent')
    if value['actual_poststage_observed']:
        _require(returned['primary_identity'] == parent['primary_manager_identity'] and
                 returned['date_pointer_identity'] == parent['game_state_identity'] + 8,
                 f'{name} returned receiver/date argument differs from actual parent')
        _require(value['same_clock_thread_order'] is
                 _ordered(parent['entry_event'], entry['event'], returned['event']),
                 f'{name} process-clock/thread/order availability or value differs')
        _require(type(value['active_parent_unchanged']) is bool,
                 f'{name} returned active parent observation unavailable')
    else:
        _require(value['same_clock_thread_order'] is None and
                 value['active_parent_unchanged'] is None,
                 f'{name} uncaptured poststage manufactures parent/order flags')
    if value['saved_mask_parent_observation_admitted'] is True:
        mask = value['actual_saved_mask']
        _require(mask in (0, 2) and parent['saved_mask02_admitted'] is (mask != 0) and
                 parent['saved_c0_observed_rva'] == _RETURN,
                 f'{name} actual saved-mask provenance differs')
        start, saved, end = parent['entry_event'], parent['saved_c0_event'], entry['event']
        _require(start['sequence'] > 0 and saved['sequence'] > 0 and
                 start['clock_identity'] != 0 and start['clock_identity'] == saved['clock_identity'] and
                 start['thread_id'] is not None and start['thread_id'] == saved['thread_id'] and
                 start['sequence'] < saved['sequence'],
                 f'{name} admitted saved-mask observation has no literal parent token')
        if (value['observed'] and end['clock_identity'] == start['clock_identity'] and
                end['thread_id'] == start['thread_id']):
            _require(saved['sequence'] < end['sequence'],
                     f'{name} literal saved-mask clock/thread/order differs')
    if parent['saved_c0_raw'] is not None and parent['saved_mask02_admitted'] is not None:
        _require(parent['saved_mask02_admitted'] is ((parent['saved_c0_raw'] & 2) != 0),
                 f'{name} independently observed fullC0 contradicts saved mask')
    _snapshot(entry, name + '.entry', value['observed'])
    _snapshot(returned, name + '.returned', value['actual_poststage_observed'])
    _require(not entry['entry_due_refs_at_return'] and
             not entry['entry_queue_extent_backing_full_ids'] and
             not entry['entry_queue_extent_backing_complete'],
             f'{name} entry snapshot manufactures returned extent')
    immutable_refs = [ref for army in entry['queued_armies']
                      for record in army['gathering_records'] for ref in record['pending_refs']]
    rereads = returned['entry_due_refs_at_return']
    _require(len(rereads) <= len(immutable_refs) and
             (not value['actual_poststage_observed'] or len(rereads) == len(immutable_refs)),
             f'{name} returned entry-ref physical reread extent differs')
    for before, after in zip(immutable_refs, rereads):
        _require(all(before[key] == after[key] for key in
                     ('source_ref_identity', 'owner_full_id', 'ordinal')),
                 f'{name} returned physical reread changes immutable entry ref/order')
    q = entry['queue158']['count']
    backing = returned['entry_queue_extent_backing_full_ids']
    complete = returned['entry_queue_extent_backing_complete']
    buffer = returned['queue158']['buffer_identity']
    if q is None or buffer is None:
        _require(not complete and not backing,
                 f'{name} unavailable entry extent/current backing was inferred')
    elif q <= 0:
        _require(not backing and (not value['actual_poststage_observed'] or complete),
                 f'{name} signed no-work returned entry extent differs')
    else:
        _require(len(backing) <= q and (not complete or len(backing) == q) and
                 (not backing or buffer != 0),
                 f'{name} returned original backing extent differs')
    if value['actual_poststage_observed'] and returned['all_declared_reads_complete'] and q is not None:
        _require(complete, f'{name} complete returned reads lose original entry extent')
    armies = (entry['queued_armies'] + entry['roster_armies'] +
              returned['queued_armies'] + returned['roster_armies'])
    _require(any(army['receiver']['resolution_complete'] and
                 army['receiver']['selected_full_id'] == full for army in armies),
             f'{name} loses exact selected full-generation query membership')
    # q<=0 and resolved combat skip are source facts, not permission to invent
    # an uncaptured return. Noncombat partial returns remain partial; independent
    # prepared/cache/physical association values never imply native refresh calls.


def validate_due_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Reject forged due semantic combinations without changing owned raw facts.

    The caller first invokes59d's exact recursive _typed('Due'). Root game/load
    epoch remains independently optional; this API never compares current query
    date, manager, clock or epoch with an immutable historical snapshot.
    """
    _require(type(value) is dict and type(expected_carmy_id) is int and
             -(1 << 31) <= expected_carmy_id < (1 << 32),
             'owned family or full CArmy ID is malformed')
    full = expected_carmy_id & _INVALID
    _require(full != _INVALID, 'invalid full CArmy ID cannot own history')
    try:
        _require(value['schema'] == 'army_gathering_due_natural_stage_12004.v1' and
                 value['source'] == 'native_gathering_due_natural_stage_12004' and
                 value['callee_rva'] == 0x2A9AF20 and value['caller_return_rva'] == _RETURN and
                 value['logical_source_end_exclusive'] == 0x2A9B579 and
                 value['source_exe_sha256'] == _SHA and value['source_locations'] == _LOCATIONS,
                 'actual source/build/locations differ')
        _require(value['refresh_cache_basis'] == 'guarded_entry_and_actual_return_fields' and
                 value['internal_refresh_callback_observed'] is False and
                 value['prediction_ready'] is False and value['whole_daily_monthly_ready'] is False,
                 'observed fields were promoted to refresh/prediction/whole readiness')
        for i, event in enumerate(value['records']):
            _event(event, full, f'records[{i}]')
    except (KeyError, TypeError, IndexError, OverflowError) as error:
        raise ValueError('gathering due expected exact pretyped DTO') from error
