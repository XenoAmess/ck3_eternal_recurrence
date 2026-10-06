"""Construction-only current prefix operands; complete states are explicit."""
from copy import deepcopy

from daily_assault_roster_admission_fixture import operand_resolution, references, state
from pre_date_dated_append_fixture import id_list
from pre_date_pending_update_fixture import source as pending_source, undemanded_setup, same_roster_standalone_source


def predicate(verdict=None, *, demanded=False):
    observed = verdict is not None
    return {'demanded': demanded, 'observable': observed, 'verdict': verdict,
            'unavailable_reason': '' if observed else 'fixture_native_callback_unavailable' if demanded else 'not_demanded'}


def occurrence(index, request, branch, *, selected=None):
    full = request if selected is None else selected
    row = {**state(True), 'native_index': index, 'original_request_full_id_u32': request,
           'army_resolution': operand_resolution(request, selected=full, fallback=full != request),
           'earlier_skip': branch == 'skip',
           'earlier_skip_source': 'same_query_existing_pending_count' if branch == 'skip' else 'pending_dispatch_bypass',
           'army_character_120_raw_u32': None, 'character_resolution': operand_resolution(),
           'army_unit_124_raw_u32': None, 'unit_resolution': operand_resolution(),
           'unit_owner_174_raw_u32': None, 'character_magic_1c_raw_u32': None,
           'character_full_id_18_raw_u32': None, 'character_death_1d0_present': None,
           'character_state_1c8_present': None, 'character_state_1c0_present': None,
           'character_state_1b8_present': None, 'membership': predicate(), 'basic_rule': predicate(),
           'availability': predicate(), 'failure_append_army_10_raw_u32': None}
    if branch == 'skip':
        return row
    row['army_character_120_raw_u32'] = 0xFFFFFFFF if branch == 'sentinel' else 0xFE000081
    if branch == 'sentinel':
        return row
    row.update(character_resolution=operand_resolution(0xFE000081, kind='character', selected=0xFE0000A1, fallback=True),
               army_unit_124_raw_u32=0xFD000041,
               unit_resolution=operand_resolution(0xFD000041, kind='unit', selected=0x01000041, fallback=True),
               unit_owner_174_raw_u32=0xFE000051, character_magic_1c_raw_u32=0 if branch == 'tag' else 0x43686172)
    if branch == 'tag':
        row['failure_append_army_10_raw_u32'] = full
        return row
    row.update(character_full_id_18_raw_u32=0xFE0000A1, character_death_1d0_present=False,
               character_state_1c8_present=branch != 'state')
    if branch == 'state':
        row.update(character_state_1c0_present=False, character_state_1b8_present=False,
                   failure_append_army_10_raw_u32=full)
        return row
    row.update(membership=predicate(True, demanded=True), basic_rule=predicate(True, demanded=True),
               availability=predicate(branch != 'availability', demanded=True))
    if branch == 'availability':
        row['failure_append_army_10_raw_u32'] = full
    return row


def source_package():
    requests = [11, 12, 0xFE00000D, 14, 15, 0xFE00000D, 16]
    rows = [occurrence(0, 11, 'skip'), occurrence(1, 12, 'sentinel'),
            occurrence(2, 0xFE00000D, 'tag', selected=13), occurrence(3, 14, 'availability'),
            occurrence(4, 15, 'pass'), occurrence(5, 0xFE00000D, 'tag', selected=13), occurrence(6, 16, 'state')]
    raw = {**state(True), 'schema_version': 1, 'source': 'native_current_pre_date_character_prefix_inputs',
           'stage': 'observed_current_conditional_2a99f72_character_prefix', 'manager_loaded': True,
           'manager_identity': 'native:7000000', 'original_roster': references(requests),
           'initial_80': id_list([7, 7]), 'occurrences': rows}
    pending = pending_source(branches=['current_zero'], roster=tuple(requests), queue=(99, 99))
    for index, row in enumerate(pending['occurrences']):
        row['original_army_resolution'] = deepcopy(rows[index]['army_resolution'])
        if index:
            row.update(pending_mutator_selected=False, army_counter_5c_raw_i32=1,
                       pending_setup=undemanded_setup(), original_arrg_references=references(), arrg_occurrences=[])
    admission = same_roster_standalone_source(pending)
    for index, row in enumerate(admission['occurrences']):
        row['original_army_resolution'] = deepcopy(rows[index]['army_resolution'])
    return {'prefix': raw, 'pending': pending, 'admission': admission}


def unavailable_availability_package():
    package = source_package()
    package['prefix'].update(state(False, 'availability_native_verdict_unavailable', partial=True))
    row = package['prefix']['occurrences'][3]
    row.update(state(False, 'availability_native_verdict_unavailable', partial=True),
               availability=predicate(demanded=True), failure_append_army_10_raw_u32=None)
    return package


def unavailable_owner_package():
    package = source_package()
    package['prefix'].update(state(False, 'unit_owner_174_raw_u32_unavailable', partial=True))
    row = package['prefix']['occurrences'][2]
    row.update(state(False, 'unit_owner_174_raw_u32_unavailable', partial=True),
               unit_owner_174_raw_u32=None, character_magic_1c_raw_u32=None, failure_append_army_10_raw_u32=None)
    return package
