"""Semantic checks after the strict owned actual consumer DTO type check.

Natural budget returns attach to the captured entry group later in the same
consumer invocation. They are independent of full B, which remains unknown.
This module never completes entry/return data from a later query.
"""
from __future__ import annotations


def _need(condition, message):
    if not condition:
        raise ValueError(f'army actual consumer: {message}')


def _ordered(first, last):
    return (first['clock_identity'] != 0
            and first['clock_identity'] == last['clock_identity']
            and 0 < first['sequence'] < last['sequence']
            and first['thread_id'] is not None
            and first['thread_id'] == last['thread_id'])


def _empty_token(value):
    return (value['clock_identity'] == 0 and value['sequence'] == 0
            and value['thread_id'] is None)


def _vector(value):
    rows = value['ordered_full_ids_u32']
    _need(len(rows) <= 128, 'vector exceeds actual owned occurrence bound')
    count, capacity = value['count_raw_i32'], value['capacity_raw_i32']
    if rows:
        _need(count is not None and capacity is not None
              and 0 <= len(rows) <= count <= capacity
              and value['data_identity'] not in (None, 0),
              'copied vector occurrences lack their native header')
    if value['references_complete']:
        _need(count is not None and capacity is not None
              and 0 <= count <= capacity and count == len(rows)
              and all(raw is not None for raw in rows),
              'complete vector loses full-ID occurrences')
        if count:
            _need(value['data_identity'] not in (None, 0),
                  'complete nonempty vector lacks its original backing')


def _resolved(value, *, returned=False):
    selected = value['selected_full_id_u32']
    if selected is not None:
        _need(value['object_identity'] not in (None, 0),
              'selected full generation lacks physical receiver')
    if value['used_fallback'] is False and not returned:
        _need(selected is not None and selected == value['requested_full_id_u32'],
              'nonfallback resolution changed the full generation')


def _table(value, *, returned, parent, consumer_return):
    controls, groups = value['physical_controls'], value['groups']
    _need(len(controls) <= 512 and len(groups) <= 32,
          'table exceeds actual owned slots/groups')
    mask, tail, end = (value['mask_raw_i32'], value['tail_distance_raw_u8'],
                       value['end_slot_raw_i32'])
    if mask is not None and tail is not None:
        computed = (mask + tail + 1) & 0xFFFFFFFF
        if computed >= 1 << 31:
            computed -= 1 << 32
        _need(end == computed, 'table physical end does not match native mask/tail')
    if controls:
        _need(end is not None and end >= len(controls)
              and value['entries_identity'] not in (None, 0),
              'physical controls lack original table extent')
    if value['controls_complete']:
        _need(end is not None and 0 <= end <= 512 and len(controls) == end
              and all(control is not None for control in controls)
              and value['end_marker_control_raw_u8'] not in (None, 0),
              'complete physical table has missing controls/end marker')
    previous_slot = -1
    previous_budget_return = None
    for index, group in enumerate(groups):
        slot = group['physical_slot_i64']
        _need(group['native_index'] == index and previous_slot < slot < len(controls)
              and controls[slot] not in (None, 0)
              and group['control_raw_u8'] == controls[slot],
              'group does not retain ordered physical slot/control identity')
        previous_slot = slot
        _vector(group['armies'])
        _vector(group['arrgs'])
        _need(not group['besieging_dependencies_complete'],
              'budget child was promoted into complete entry B')
        if returned:
            _need(not group['army_occurrences']
                  and not group['armies']['references_complete']
                  and not group['arrgs']['references_complete']
                  and not group['armies']['ordered_full_ids_u32']
                  and not group['arrgs']['ordered_full_ids_u32'],
                  'returned payload-free table backfills entry dependencies')
            _need(all(field is None for field in group['siege_resolution'].values())
                  and all(group[field] is None for field in (
                      'province_identity', 'province_magic_raw_u32',
                      'province_full_id_u32', 'breach_level_raw_i32')),
                  'returned group introduces uncaptured siege/province dependencies')
        else:
            resolution = group['siege_resolution']
            _resolved(resolution)
            _need(resolution['requested_full_id_u32'] == group['siege_full_id_u32'],
                  'siege resolution changed the original requested full ID')
            occurrences = group['army_occurrences']
            army_ids = group['armies']['ordered_full_ids_u32']
            _need(len(occurrences) == len(army_ids),
                  'army occurrences were removed or filled from another frame')
            for ordinal, army in enumerate(occurrences):
                _need(army['native_index'] == ordinal
                      and army['resolution']['requested_full_id_u32'] == army_ids[ordinal],
                      'army occurrence loses native order/full generation')
                _resolved(army['resolution'])
                _vector(army['regiment_roster'])
                _need(army['native_whole_current_soldiers'] is None,
                      'uncalled whole-army scalar was substituted for B')
        observed = group['natural_budget_observed']
        if observed:
            _need(not returned and group['native_current_expected_loss'] is not None,
                  'budget scalar has no actual child return at its captured entry group')
            _need(parent['exact_post_date_parent']
                  and _ordered(parent['entry_event'], group['budget_entry_event'])
                  and _ordered(group['budget_entry_event'], group['budget_returned_event'])
                  and _ordered(group['budget_returned_event'], consumer_return),
                  'natural budget child crosses consumer clock/thread/entry-return extent')
            if previous_budget_return is not None:
                _need(_ordered(previous_budget_return, group['budget_entry_event']),
                      'budget children changed captured physical group order')
            previous_budget_return = group['budget_returned_event']
            resolution = group['siege_resolution']
            _need(resolution['object_identity'] not in (None, 0)
                  and resolution['selected_full_id_u32'] is not None
                  and group['province_identity'] not in (None, 0)
                  and group['province_full_id_u32'] is not None,
                  'budget append lacks exact captured siege/province receiver join')
        else:
            _need(group['native_current_expected_loss'] is None
                  and _empty_token(group['budget_entry_event'])
                  and _empty_token(group['budget_returned_event']),
                  'missing natural budget was replaced by query/final-scalar data')
    if value['raw_references_complete']:
        _need(not returned and value['controls_complete']
              and len(groups) == sum(control != 0 for control in controls)
              and all(group['armies']['references_complete']
                      and group['arrgs']['references_complete'] for group in groups),
              'complete entry references omit physical occupied groups')


def _regiment_complete(row):
    return (row['identity_valid'] is not None
            and (not row['identity_valid']
                 or (row['current_soldiers'] is not None
                     and row['maximum_soldiers'] is not None
                     and row['native_loss_writer_skipped'] is not None
                     and row['data_complete'])))


def _regiment_records(row):
    records = row['data_records']
    _need(len(records) <= 1024, 'DATA records exceed actual copied bound')
    for index, data in enumerate(records):
        _need(data['native_index'] == index
              and data['persistent_resolution']['requested_full_id_u32']
                  == data['persistent_full_id_u32'],
              'DATA loses native index or persistent full-generation request')
        _resolved(data['persistent_resolution'])
        physical = data['physical']
        if physical is not None:
            ordinal = data['data_chunk_ordinal']
            selected = data['persistent_resolution']['object_identity']
            _need(data['persistent_identity_valid'] is True
                  and ordinal is not None and 0 <= ordinal < 7
                  and selected not in (None, 0)
                  and physical['object_identity'] == selected + 0x18 + ordinal * 0x24,
                  'physical DATA chunk does not derive from captured receiver/ordinal')
            ready = all(physical[key] is not None for key in (
                'maximum_soldiers', 'current_soldiers', 'persistent_regiment_id',
                'own_chunk_ordinal', 'army_regiment_id', 'state_raw_i32'))
            _need(data['ready'] == ready, 'DATA readiness differs from copied physical fields')
        else:
            _need(not data['ready'], 'missing physical chunk was labelled ready')


def _same_data_records(before, after):
    a, z = before['data_records'], after['data_records']
    if len(a) != len(z):
        return False
    for first, last in zip(a, z):
        if (first['persistent_full_id_u32'] != last['persistent_full_id_u32']
                or first['data_chunk_ordinal'] != last['data_chunk_ordinal']
                or first['physical'] is None or last['physical'] is None):
            return False
        if any(first['physical'][key] != last['physical'][key] for key in (
                'object_identity', 'persistent_regiment_id',
                'own_chunk_ordinal', 'army_regiment_id')):
            return False
    return True


def _regiments(event):
    entry, returned = event['entry_regiments'], event['returned_regiments']
    _need(len(entry) <= 256 and len(returned) <= len(entry),
          'returned regiment records are not the captured entry prefix')
    _need(sum(len(row['data_records']) for row in entry) <= 1024
          and sum(len(row['data_records']) for row in returned) <= 1024,
          'DATA records exceed the shared native entry/returned capture budget')
    for row in entry:
        _resolved(row['resolution'])
        _regiment_records(row)
        _need(row['same_instance_after'] is None and row['same_data_header_after'] is None,
              'entry regiment was backfilled from the returned stage')
    for before, after in zip(entry, returned):
        _resolved(after['resolution'], returned=True)
        _regiment_records(after)
        a, z = before['resolution'], after['resolution']
        _need(a['object_identity'] == z['object_identity']
              and a['requested_full_id_u32'] == z['requested_full_id_u32']
              and a['used_fallback'] == z['used_fallback'],
              'returned regiment replaced the captured physical/full-ID request')
        same = (z['selected_full_id_u32'] is not None
                and z['selected_full_id_u32'] == a['selected_full_id_u32'])
        _need(after['same_instance_after'] == same,
              'returned full-generation reuse flag differs from observed identity')
        same_header = all(before[key] == after[key] for key in (
            'data_identity', 'data_capacity_raw_i32', 'data_count_raw_i32'))
        _need(after['same_data_header_after'] == same_header,
              'returned DATA-header flag differs from original header')
    if event['entry_dependencies_complete']:
        table = event['entry_table']
        _need(table['raw_references_complete']
              and table['occupied_count_raw_i32'] == len(table['groups'])
              and event['entry_pending_queue']['references_complete']
              and not event['capture_failure_flags'] & 2
              and all(_regiment_complete(row) for row in entry)
              and all(army['resolution']['selected_full_id_u32'] is not None
                      and army['regiment_roster']['references_complete']
                      for group in table['groups'] for army in group['army_occurrences']),
              'narrow entry completeness lacks captured roster/table dependencies')
    if event['returned_dependencies_complete']:
        _need(event['entry_dependencies_complete']
              and _ordered(event['parent']['entry_event'], event['returned_event'])
              and event['returned_table']['controls_complete']
              and event['returned_pending_queue']['references_complete']
              and len(returned) == len(entry)
              and all(row['same_instance_after'] and row['same_data_header_after']
                      and _regiment_complete(row) for row in returned)
              and all(_same_data_records(before, after)
                      for before, after in zip(entry, returned)),
              'narrow returned completeness lacks its original entry/return join')


def validate_consumer_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Validate source relationships after the Consumer DTO runs _typed.

    Empty/partial observations remain valid; an unobserved scalar stays null.
    The retained full IDs are compared without discarding generation bits.
    """
    _need(type(expected_carmy_id) is int and 0 <= expected_carmy_id <= 0xFFFFFFFF,
          'expected CArmy full ID is not an exact unsigned32 integer')
    full = expected_carmy_id
    _need(value['schema_version'] == 1
          and value['source'] == 'native_actual_assault_consumer_entry_return'
          and value['membership_basis'] == 'captured_entry_group_army_full_ids',
          'family source or original entry membership basis differs')
    _need(value['observer_installed'] == value['current_session_guard'],
          'current journal guard differs from its installed observer')
    latest = value['latest_journal_sequence']
    _need(value['overwritten_events'] == max(0, latest - 8) and len(value['events']) <= 8,
          'journal retained range differs from the actual eight-event ring')
    previous = max(0, latest - 8)
    for event in value['events']:
        sequence = event['journal_sequence']
        _need(previous < sequence <= latest, 'journal order/range lost an actual event')
        previous = sequence
        parent = event['parent']
        _need(event['capture_stage'] == 'natural_2A97EB0_entry_and_return'
              and parent['actual_entry_rva'] == 0x2A97EB0
              and parent['caller_return_rva'] == 0x2A9A8EA
              and parent['manager_identity'] != 0 and not parent['active'],
              'consumer original source/returned parent boundary differs')
        _need(event['original_called'] and event['original_returned'],
              'published consumer event lacks its naturally returned original')
        if parent['exact_post_date_parent']:
            _need(_ordered(parent['phase_entry_event'], parent['entry_event']),
                  'consumer parent does not follow its exact post-date clock/thread')
        if event['actual']:
            _need(event['current_session_guard'] and parent['exact_post_date_parent']
                  and _ordered(parent['entry_event'], event['returned_event']),
                  'actual entry/return lacks ordered original clock/thread evidence')
        _need(event['actual'] == (event['current_session_guard']
              and parent['exact_post_date_parent'] and event['original_returned']),
              'actual flag differs from its source guard')
        _need(not event['full_daily'] and not event['full_monthly']
              and not event['conditional_stage_binding_ready'],
              'independent missing full B/prior-write proof was promoted')
        _need(any(full in group['armies']['ordered_full_ids_u32']
                  for group in event['entry_table']['groups']),
              'query full-generation subject is absent from original entry membership')
        _table(event['entry_table'], returned=False, parent=parent,
               consumer_return=event['returned_event'])
        _table(event['returned_table'], returned=True, parent=parent,
               consumer_return=event['returned_event'])
        _vector(event['entry_pending_queue'])
        _vector(event['returned_pending_queue'])
        _regiments(event)
