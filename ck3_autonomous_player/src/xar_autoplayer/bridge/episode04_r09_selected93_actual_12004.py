"""Pure reader for the exact R0176 selected93 micro experiment.

The single observed role exception is deliberately local to this experiment.
No action, raw-file access, birth/refill inference or full-card qualification.
"""
from xar_autoplayer.bridge import army_split_merge_observation_12004 as observation
from xar_autoplayer.bridge import army_split_transfer_assertions_12004 as transfer

MACHINE = 'desktop-3fevhd2-1c74096080'
SOURCE = 'dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb'
HELPER = '074f79354632f937d7a8004eda1e896c28d337df05024a02bb2e424a9376227f'


def _need(value, reason):
    if not value:
        raise ValueError(reason)


def qualify_r0176_selected93_micro_12004(projection):
    """Recompute selected DATA, exact role transition and independent commanders.

    Input may be the portable literal projection or the same named saved packet
    wrappers. Artifact integrity and original SDK receipts remain separate from
    this pure semantic reader. This API never opens a path or submits a query.
    """
    _need(projection.get('machine_id') == MACHINE, 'source machine is not the recorded machine')
    failure = projection.get('strict_failure_literal', {})
    _need(failure.get('machine_id') == MACHINE and failure.get('stage') == 'post-split'
          and failure.get('error') == 'unrelated Army cohort changed'
          and failure.get('action_retry_allowed') is False,
          'the actual strict failure must remain explicit')
    stages = [projection['stages'][key] for key in ('baseline', 'post_split', 'post_merge')]
    binding = stages[0]['binding']
    _need(failure.get('binding') == binding, 'preserved failure lifecycle differs')
    for stage in stages:
        _need(stage.get('machine_id') == MACHINE and stage.get('source_head') == SOURCE
              and stage.get('run_id') == MACHINE + '--vanilla--R0176'
              and stage.get('binding') == binding and stage.get('helper', {}).get('sha256') == HELPER,
              'saved lifecycle/source/helper differs')
    b, s, m = [stage['packet'] for stage in stages]
    rows = [{a['army_id']: a for a in p['query']['army_strengths']} for p in (b, s, m)]
    pre, split, merged = rows
    for p, mapped in zip((b, s, m), rows):
        frame, query = p['frame'], p['query']
        _need(query.get('accepted') is True and query.get('queried_snapshot_id') == frame['snapshot_id']
              and query.get('queried_revision') == frame['revision']
              and query.get('queried_native_revision') == frame['native_revision'],
              'strengths do not belong to independent frame')
        _need(len(mapped) == len(query['army_strengths']), 'duplicate Army strength row')
        full_roster = {a['army_id'] for a in frame['player_armies']}
        _need(set(mapped) == full_roster and {i for i, a in mapped.items() if a['status'] == 'available'}
              == full_roster - {16777321}, 'query scope or available subset differs from full roster')
        _need(mapped[16777321]['status'] == 'unavailable'
              and mapped[16777321]['unavailable_reason'] == 'native_carmy_not_found'
              and mapped[16777321].get('native_carmy_id') is None,
              'unavailable full-query row was reclassified')
        excluded = p['excluded_unavailable_cohorts']
        _need(len(excluded) == 1 and excluded[0]['army_id'] == 16777321
              and excluded[0]['unavailable_reason'] == 'native_carmy_not_found'
              and excluded[0]['strengths_qualified'] is False
              and excluded[0]['troop_values_filled_with_zero'] is False,
              'unavailable row acquired an invented strength qualification')
        _need(excluded[0]['snapshot_roster_binding'] == b['excluded_unavailable_cohorts'][0]['snapshot_roster_binding'],
              'unavailable Army identity/owner/position changed')
    selected = transfer.assert_fresh_split_transfer_12004(
        b['frame'], s['frame'], source_army_id=93, pre_strengths=b['query'], post_strengths=s['query'],
        pre_commander=b['commanders']['93'], post_commanders={int(k): v for k, v in s['commanders'].items()})
    _need(selected['accepted'] and selected['identity']['sibling_army_id'] == 162
          and selected['identity']['native_carmy_ids'] == {93: 85, 162: 155},
          'split identity or selected physical DATA differs')
    observations = [transfer._observe([a for a in mapped.values() if a['status'] == 'available']) for mapped in rows]
    old, middle, final = [value[0] for value in observations]
    _need(observations[0][1:] == observations[1][1:] == observations[2][1:],
          'all available physical DATA values or ArRg occurrences changed')
    _need(set(old)-set(middle) == {59} and not set(middle)-set(old)
          and set(final) == set(middle), 'ArRg change is not the single observed removed59')
    removed = old[59]
    role = removed['data'].get('native_character_role_v1', {})
    _need(removed['army_id'] == 18 and transfer._empty_character(removed)
          and role.get('resolved_character_id') == role.get('character_raw_id_148') == 34232
          and role.get('native_carmy_id') == role.get('arrg_army_id_140') == 18
          and role.get('extension_arrg_id_f8') == 59 and role.get('extension_army_id_f4') == -1,
          'removed record is not exact emptyDATA/cache1/1/Character34232 ArRg59')
    for key in set(old) & set(middle):
        _need(old[key]['strength'] == middle[key]['strength']
              and old[key]['data']['records'] == middle[key]['data']['records']
              and old[key]['data'].get('native_loss_writer_skipped') == middle[key]['data'].get('native_loss_writer_skipped'),
              'split changed another original ArRg cache/DATA/predicate')
    for army in (94, 95):
        for first, last in ((pre, split), (split, merged)):
            _need(observation.compare_split_merge_cohorts([first[army]], [last[army]])['frozen_exact_cohort_pass'],
                  'unrelated94/95 cohort changed')
    _need(observation.compare_split_merge_cohorts([split[18]], [merged[18]])['frozen_exact_cohort_pass'],
          'Army18 changed during merge')
    def current(packet, army, native):
        return observation.read_bound_current_commander(packet['commanders'][str(army)], packet['frame'],
                                                       army_id=army, native_carmy_id=native)
    _need(all(current(p, 18, 18) == 31254 for p in (b, s, m)), 'Army18 actual commander changed')
    _need(current(b, 93, 85) is None and current(s, 93, 85) is None
          and current(s, 162, 155) == current(m, 93, 85) == 34232,
          'independent assigned commander readbacks differ')
    observation._fresh_pair(s['frame'], m['frame'])
    _need(set(observation._roster(s['frame'])) - set(observation._roster(m['frame'])) == {162}
          and not set(observation._roster(m['frame'])) - set(observation._roster(s['frame']))
          and merged[93]['native_carmy_id'] == 85, 'merge removal/survivor identity differs')
    cohort = observation.compare_split_merge_cohorts([split[93], split[162]], [merged[93]])
    _need(cohort['frozen_exact_cohort_pass'] and cohort['original_ids'] == [673, 674, 675, 676]
          and cohort['whole_after_current_max'] == [250, 250], 'selected merge cohort changed')
    selected_observations = [transfer._observe([pre[93]]), transfer._observe([split[93], split[162]]),
                             transfer._observe([merged[93]])]
    _need(all([sum(v[i] for v in item[1].values()) for i in (0, 1)] == [250, 250]
              for item in selected_observations), 'selected physical totals differ')
    _need(all(not transfer._empty_character(row) for row in selected_observations[-1][0].values()),
          'merge added an empty Character1/1 row')
    return {'accepted': True, 'read_only': True, 'machine_id': MACHINE,
            'source_army_id': 93, 'fresh_sibling_army_id': 162, 'fresh_sibling_native_carmy_id': 155,
            'physical_current_max_before_split_after_split_after_merge': [[250, 250]] * 3,
            'all_available_physical_DATA_and_occurrences_conserved': True,
            'strict_unrelated_freeze_pass': False, 'preserved_strict_failure_required': True,
            'exact_empty_role_removed': {'army_id': 18, 'army_regiment_id': 59, 'character_id': 34232},
            'actual_merge_survivor_commander_id': 34232, 'new_empty_Character_1_1_at_merge': [],
            'all_roster_strengths_qualified': False, 'excluded_unavailable_army_ids': [16777321],
            'actual_source_PC_execution_observed': False, 'birth_producer_observed': False,
            'actual_physical_refill': None, 'native_Knight_membership': None,
            'dynamic_video_qualification': False, 'R09_full_card_closed': False}
