"""Opt-in owned subject closure and raw seven-slot deltas, never a core replay."""
from __future__ import annotations
from copy import deepcopy

COVERAGE = 'subject_coverage_v1'
MODE = 'explicit_full_carmy_physical_closure'
OMISSION = 'scoped_capture_omits_unselected_physical_context'
_RAW_FIELDS = ('physical_index', 'current_soldiers', 'maximum_soldiers',
               'owner_persistent_regiment_id', 'q_ordinal_raw',
               'army_regiment_id_raw', 'exclusion_byte_14_raw', 'state_raw')

def _need(condition, reason):
    if not condition:
        raise ValueError('subject_coverage_v1 ' + reason)

def validate_subject_physical_frame_12004(frame, *, expected_carmy_id):
    """Validate an already typed CoreFrame; return its qualified owned closure."""
    if COVERAGE not in frame:
        return None
    coverage = frame[COVERAGE]
    requested = coverage['requested_full_carmy_ids']
    _need(coverage['schema_version'] == 1 and coverage['mode'] == MODE, 'schema or mode')
    _need(coverage['scope_epoch'] > 0 and coverage['bound_game_state_identity'] > 0,
          'positive scope epoch and GameState identity required')
    _need(coverage['bound_owner_character_id'] > 0, 'positive bound owner required')
    _need(0 < len(requested) <= 64 and len(set(requested)) == len(requested) and -1 not in requested,
          'one to 64 unique full generation requests required')
    _need(any((value & 0xFFFFFFFF) == expected_carmy_id for value in requested),
          'queried full CArmy generation outside explicit scope')
    missing = coverage['missing_inputs']
    _need(all(reason != '' for reason in missing) and len(set(missing)) == len(missing),
          'missing reasons must be unique and nonempty')
    witnesses = coverage['subject_identity_witnesses']
    _need([value['full_carmy_id'] for value in witnesses] == requested,
          'witnesses must retain requested order and extent')
    _need(frame['capture_complete'] is False and OMISSION in frame['missing_inputs'],
          'scoped capture cannot claim global completeness')
    if coverage['manager_occurrences_complete']:
        for name in ('persistent', 'army_refresh'):
            rows = frame[name + '_occurrences']
            count = frame['native_' + name + '_occurrence_count']
            _need(count is not None and count >= 0 and len(rows) == count
                  and all(row['raw_full_id'] is not None for row in rows),
                  'complete original ' + name + ' roster required')
    if not coverage['physical_closure_complete']:
        return None
    owner = coverage['bound_owner_character_id']
    for witness in witnesses:
        full = witness['full_carmy_id']
        unit = witness['public_unit_id']
        _need(witness['resolved_full_carmy_id'] == full
              and witness['carmy_magic_14_raw'] == 0x41726D79
              and unit is not None and unit != -1
              and witness['unit_resolved_full_id'] == unit
              and witness['unit_magic_14_raw'] == 0x556E6974
              and witness['unit_owner_character_id'] == owner
              and witness['unit_full_carmy_id'] == full,
              'complete CArmy and Unit identity witness required')
    objects = {value['physical_token']: value for value in frame['army_objects']}
    persistents = {value['physical_token']: value for value in frame['persistent_objects']}
    targets = {}
    for full in requested:
        occurrences = [row for row in frame['army_refresh_occurrences'] if row['raw_full_id'] == full]
        _need(occurrences and all(row['resolved_full_id'] == full and row['used_fallback'] is False
              and row['physical_token'] and not row['unavailable_reason'] for row in occurrences),
              'requested Army original occurrence must resolve exact generation without fallback')
        tokens = {row['physical_token'] for row in occurrences}
        _need(len(tokens) == 1, 'one requested generation has multiple physical Army identities')
        token = next(iter(tokens))
        army = objects.get(token)
        _need(army is not None and army['resolved_full_id'] == full and not army['unavailable_reason'],
              'requested Army physical copy missing')
        arrgs = army['arrg_occurrences']
        _need(army['native_arrg_occurrence_count'] is not None
              and army['native_arrg_occurrence_count'] >= 0
              and len(arrgs) == army['native_arrg_occurrence_count'], 'complete requested Army ArRg roster required')
        physical = {}
        links = []
        for arrg in arrgs:
            occurrence = arrg['occurrence']
            _need(occurrence['raw_full_id'] is not None
                  and occurrence['resolved_full_id'] == occurrence['raw_full_id']
                  and occurrence['used_fallback'] is False and occurrence['physical_token']
                  and not occurrence['unavailable_reason'], 'exact requested ArRg generation required')
            _need(arrg['native_refresh_admitted'] is not None and arrg['records_complete']
                  and not arrg['unavailable_reason'], 'requested ArRg raw branch and DATA incomplete')
            records = arrg['records']
            if arrg['native_refresh_admitted']:
                _need(arrg['native_loss_writer_skipped'] is False,
                      'Character override has no captured raw DATA closure')
                _need(arrg['native_record_count'] is not None and arrg['native_record_count'] >= 0
                      and len(records) == arrg['native_record_count'], 'complete admitted DATA extent required')
            links.append((occurrence['physical_token'], occurrence['resolved_full_id'],
                          arrg['native_refresh_admitted'], arrg['native_loss_writer_skipped'],
                          tuple((row['persistent_regiment_id'], row['chunk_index'], row['persistent_physical_token'])
                                for row in records)))
            for record in records:
                p = persistents.get(record['persistent_physical_token'])
                _need(record['native_record_admitted'] and p is not None
                      and p['resolved_full_id'] == record['persistent_regiment_id']
                      and p['resolved_full_id'] not in (None, -1) and not p['unavailable_reason'],
                      'exact admitted persistent physical receiver missing')
                values = p['physical_values']
                chunks = values['chunks']
                _need(not values['unavailable_reason'] and len(chunks) == 7
                      and [chunk['physical_index'] for chunk in chunks] == list(range(7)),
                      'complete raw physical seven required')
                index = record['chunk_index']
                _need(index is not None and 0 <= index < 7
                      and record['state_raw'] == chunks[index]['state_raw'],
                      'DATA physical slot and raw state binding required')
                physical[p['physical_token']] = p
        targets[full] = {'army_token': token, 'links': links, 'physical': physical}
    if not coverage['manager_occurrences_complete'] or missing:
        return None
    return {'coverage': coverage, 'targets': targets}

def project_subject_raw_physical_delta_12004(event, *, expected_carmy_id):
    """Return no field for legacy input; never replay or attribute the native core."""
    if not any(COVERAGE in event[name] for name in ('entry', 'returned')):
        return None
    result = {'schema_version': 1, 'subject_full_carmy_id_u32': expected_carmy_id,
              'basis': 'owned_same_core_entry_and_return_raw_physical_seven',
              'status': 'unavailable', 'physical_objects': [], 'missing_inputs': [],
              'actual_ADD_observed': False, 'causal_attribution_ready': False,
              'full_manager_ready': False, 'full_monthly_ready': False,
              'conditional_entry_projection_used': False}
    try:
        _need(all(COVERAGE in event[name] for name in ('entry', 'returned')), 'both independent frame coverages required')
        before = validate_subject_physical_frame_12004(event['entry'], expected_carmy_id=expected_carmy_id)
        after = validate_subject_physical_frame_12004(event['returned'], expected_carmy_id=expected_carmy_id)
        _need(before is not None and after is not None, 'both raw subject closures must independently qualify')
        from .army_observed_phase_contract_12004 import _ordered
        scope = event['parent_scope']
        _need(event['observed'] and event['original_called'] and event['original_returned']
              and event['entry_provenance_complete'] and event['return_provenance_complete']
              and scope['observed'] and scope['phase'] == 'post_date'
              and scope['actual_entry_rva'] == 0x2A9A570
              and event['caller_return_rva'] == 0x2A9A8E2
              and scope['primary_manager_identity'] == event['manager_identity']
              and scope['secondary_manager_identity'] == event['manager_identity'] + 8
              and scope['saved_mask02_admitted'] is True
              and scope['saved_c0_observed_rva'] == 0x2A9A8E2
              and _ordered(scope['entry_event'], event['entry_event'])
              and _ordered(event['entry_event'], scope['saved_c0_event'])
              and _ordered(scope['saved_c0_event'], event['returned_event'])
              and event['entry_date_raw'] is not None
              and event['entry_date_raw'] == event['returned_date_raw'] == scope['date_raw'],
              'same natural parent date clock thread and independent return proof required')
        binding = ('scope_epoch', 'bound_game_state_identity', 'bound_owner_character_id', 'requested_full_carmy_ids')
        _need(all(before['coverage'][key] == after['coverage'][key] for key in binding), 'scope binding changed across frames')
        _need(before['coverage']['bound_game_state_identity'] == scope['game_state_identity'], 'bound GameState differs from natural parent')
        _need(before['coverage']['subject_identity_witnesses'] == after['coverage']['subject_identity_witnesses'],
              'subject identity witness changed across frames')
        for full in before['targets']:
            left, right = before['targets'][full], after['targets'][full]
            _need(left['army_token'] == right['army_token'] and left['links'] == right['links'],
                  'requested Army ArRg or DATA identity changed across frames')
            _need(set(left['physical']) == set(right['physical'])
                  and all(left['physical'][token]['resolved_full_id'] == right['physical'][token]['resolved_full_id']
                          for token in left['physical']), 'physical pointer or full generation changed across frames')
        full = next(value for value in before['targets'] if (value & 0xFFFFFFFF) == expected_carmy_id)
        left, right = before['targets'][full]['physical'], after['targets'][full]['physical']
        for token, physical in left.items():
            slots = []
            for first, last in zip(physical['physical_values']['chunks'], right[token]['physical_values']['chunks']):
                slots.append({'physical_index': first['physical_index'],
                    'before_raw': {key: first[key] for key in _RAW_FIELDS},
                    'returned_raw': {key: last[key] for key in _RAW_FIELDS},
                    'delta_current_soldiers': last['current_soldiers'] - first['current_soldiers'],
                    'delta_maximum_soldiers': last['maximum_soldiers'] - first['maximum_soldiers']})
            result['physical_objects'].append({'physical_token': token,
                'persistent_full_id': physical['resolved_full_id'], 'chunks': slots})
        result.update(status='available', scope_binding={key: deepcopy(before['coverage'][key]) for key in binding})
    except ValueError as error:
        result['missing_inputs'] = [str(error)]
    return result
