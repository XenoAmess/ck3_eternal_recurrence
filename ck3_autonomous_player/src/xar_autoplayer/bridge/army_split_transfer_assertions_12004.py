"""Fresh split postconditions: whole ArRg transport, physical DATA, and roles.

Consumes normalized native packets only. This is not a command, a source-only
forecast, a birth observer, a Knight membership query, or a refill qualification.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from xar_autoplayer.bridge.army_replenishment_records_contract import (
    normalize_regiment_replenishment_records_v1,
)
from xar_autoplayer.bridge.army_split_merge_observation_12004 import (
    compare_split_merge_cohorts, identify_split_sibling, read_bound_current_commander,
)


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _int(value: object, name: str) -> int:
    _need(type(value) is int and -(2**31) <= value < 2**31 and value != -1,
          name + ' must be a complete native int32 ID')
    return value


def _selected(packet, identities):
    rows = {row['army_id']: row for row in packet['army_strengths']}
    return [rows[identity] for identity in identities]


def _observe(armies):
    regiments, physical, occurrences = {}, {}, Counter()
    for army in armies:
        native_army = _int(army.get('native_carmy_id'), 'CArmy')
        normalized = normalize_regiment_replenishment_records_v1(
            army['regiment_replenishment_records_v1'])
        data = {row['army_regiment_id']: row for row in normalized}
        for strength in army['regiment_strengths']:
            identity = _int(strength['army_regiment_id'], 'ArRg')
            row = data[identity]
            role = row.get('native_character_role_v1')
            if role is not None:
                _need(role['native_carmy_id'] == native_army,
                      'Character leaf is attached to another CArmy generation')
            signature = []
            for record in row['records']:
                _need(record['status'] == 'available', 'physical DATA is partial')
                key = (_int(record['persistent_regiment_id'], 'persistent Regi'),
                       record['chunk_index'])
                _need(type(key[1]) is int and 0 <= key[1] < 7,
                      'physical chunk index outside source array')
                _need(record.get('chunk_army_regiment_id') == identity,
                      'physical chunk lacks its observed ArRg backlink')
                value = (record['current_soldiers'], record['maximum_soldiers'], record['state_raw'])
                _need(all(type(item) is int for item in value)
                      and min(value[:2]) >= 0, 'physical DATA values unavailable')
                _need(key not in physical or physical[key] == value,
                      'aliased physical chunk observations disagree')
                physical[key] = value
                occurrences[(identity, *key)] += 1
                signature.append((key, value))
            _need(identity not in regiments, 'ArRg appears in both split armies')
            regiments[identity] = {'army_id': army['army_id'], 'data': row,
                                   'strength': strength, 'signature': signature}
    return regiments, physical, occurrences


def _empty_character(record):
    data, strength = record['data'], record['strength']
    role = data.get('native_character_role_v1')
    return (data['native_data_record_count'] == 0 and data['records'] == []
            and data.get('native_loss_writer_skipped') is True
            and role is not None and role['status'] == 'available'
            and role['same_ArRg_instance_after'] is True
            and role['native_character_predicate'] is True
            and type(role['resolved_character_id']) is int
            and role['resolved_character_id'] != -1
            and (strength['current_soldiers'], strength['maximum_soldiers']) == (1, 1))


def assert_fresh_split_transfer_12004(
    before: Mapping[str, object], after: Mapping[str, object], *,
    source_army_id: int, pre_strengths: Mapping[str, object],
    post_strengths: Mapping[str, object], pre_commander: Mapping[str, object],
    post_commanders: Mapping[int, Mapping[str, object]],
) -> dict[str, object]:
    """Bind actual frames/Army IDs, then report conservation or a named refusal.

    Schema/identity/query failures raise. A complete but changed physical cohort
    returns accepted=False with actual differences, without recommending a retry.
    Duplicate aliases of the same physical chunk are counted once for totals,
    while per-ArRg occurrence/order remains an independent invariant.
    """
    identity = identify_split_sibling(
        before, after, source_army_id=source_army_id,
        pre_strengths=pre_strengths, post_strengths=post_strengths)
    sibling = identity['sibling_army_id']
    original = _selected(pre_strengths, [source_army_id])
    children = _selected(post_strengths, [source_army_id, sibling])
    # Public comparison validates complete ArRg/DATA roster and actual cache sums.
    cache = compare_split_merge_cohorts(original, children)
    old, old_physical, old_occurrences = _observe(original)
    new, new_physical, new_occurrences = _observe(children)
    old_commander = read_bound_current_commander(
        pre_commander, before, army_id=source_army_id,
        native_carmy_id=original[0]['native_carmy_id'])
    actual_commanders = {}
    for army in children:
        public = army['army_id']
        _need(public in post_commanders, 'each split child needs an actual commander readback')
        actual_commanders[public] = read_bound_current_commander(
            post_commanders[public], after, army_id=public,
            native_carmy_id=army['native_carmy_id'])
    added, removed = sorted(set(new)-set(old)), sorted(set(old)-set(new))
    changed_data = sorted(i for i in set(old) & set(new)
                          if old[i]['signature'] != new[i]['signature'])
    changed_physical = sorted(key for key in set(old_physical) & set(new_physical)
                              if old_physical[key] != new_physical[key])
    missing_physical = sorted(set(old_physical)-set(new_physical))
    added_physical = sorted(set(new_physical)-set(old_physical))
    explained_added = [i for i in added if _empty_character(new[i])]
    explained_removed = [i for i in removed if _empty_character(old[i])]
    reasons = []
    if changed_physical: reasons.append('physical_chunk_values_changed')
    if missing_physical: reasons.append('physical_chunks_missing')
    if added_physical: reasons.append('physical_chunks_added')
    if changed_data: reasons.append('original_ArRg_DATA_identity_order_or_values_changed')
    if old_occurrences != new_occurrences: reasons.append('DATA_occurrence_or_ArRg_backlink_changed')
    if len(explained_added) != len(added) or len(explained_removed) != len(removed):
        reasons.append('unexplained_ArRg_birth_or_removal')
    def totals(values):
        return [sum(value[index] for value in values.values()) for index in (0, 1)]
    accepted = not reasons
    return {'accepted': accepted, 'reasons': reasons, 'read_only': True,
            'identity': identity,
            'whole_ArRg_DATA_transport_observed': accepted,
            'unique_physical_before_current_max': totals(old_physical),
            'unique_physical_after_current_max': totals(new_physical),
            'changed_physical_chunks': changed_physical,
            'missing_physical_chunks': missing_physical,
            'added_physical_chunks': added_physical,
            'added_empty_character_1_1_ids': explained_added,
            'removed_empty_character_1_1_ids': explained_removed,
            'whole_cache_before_current_max': cache['original_before_current_max'],
            'whole_cache_after_current_max': cache['whole_after_current_max'],
            'changed_original_cache_ids': cache['changed_original_strength_ids'],
            'changed_original_character_predicate_ids': cache['changed_original_character_predicate_ids'],
            'cache_exact_half_required': False,
            'actual_commander_before': old_commander,
            'actual_commanders_after': actual_commanders,
            'native_knight_membership': None,
            'birth_producer_observed': False,
            'physical_soldier_write_observed': False,
            'actual_physical_refill': None,
            'agent_conclusion': ('FRESH_SPLIT_DATA_CONSERVED_WITH_SEPARATE_ROLES'
                                 if accepted else 'SPLIT_POSTCONDITION_REFUSED'),
            'video_claim': ('Fresh split readbacks conserve the observed physical DATA cohort; '
                            'listed empty Character records are separate cache changes.'
                            if accepted else None)}
