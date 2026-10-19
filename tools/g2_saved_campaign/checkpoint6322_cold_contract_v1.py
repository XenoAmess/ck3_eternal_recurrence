"""Finite C15 rollback and abnormal-closure contract for actual checkpoint6322.

This reads bounded closed JSON only. It neither opens Driver/SAVE bodies nor
changes old ledgers. The original canonical validator owns actual SAVE loading.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
PINS = {
    'original_state': (5800, '1ab8651a69b93d73b4c77e20ae2b6d5fbf917fcecd663d4e21d44234e0703c89'),
    'original_governance': (480, '6de21b9eb306a1e0c28fed224ffd838aa6a4a70c99ebb7248bbab0116103b5b8'),
    'rollback_frontier': (50167, '0052ae0b2dfc7858b53271022adde77ebb156c3bb34fd6b5fbec7ddc039470fd'),
    'save_response': (10282, '51c530a5cbfc34bb46989a6840f84e80469022fb031478185f9dfe4874b5dcb1'),
    'saved_semantic_response': (64654, '86dfcd3d568357a50308af6a21e2e190c42d1eca0eadabf7d0cfa48d19af110b'),
    'abnormal_display_closure': (9674, 'ce0f5a9a3b38a04a139e95843f0a323f3bbd6a89074b5094fcc1ba6deb800c35'),
    'abnormal_supervisor_closure': (9921, '93c28466d55036b2e8d3abfe7774dcda52ee5dc2e78d53217e33846a6f005376'),
}
SIDECARS = {
    'faction-gift-pending-v1.json': (257, '47b63483f700c7c2d0daa55420759c4d6f7f4a7f49cb01273db483f33c522a0c'),
    'active-scheme-sway-formal-private-v1.json': (10285, 'a2d8b030b1e3c559540581f5187f74da23d9c8168af3abba0098e6ce969da178'),
    'ordinary-sway-schedule-v1.json': (390, '4ad36f1d700806315259ecec91b80fdcb8b266e9198c5319cdd78df9bef6dab0'),
}
SAVE_SHA = 'a558c776c243007f4fcb384145c63ea1ec37147a0107c4379c36c07e821a0ac6'
ACTOR = 40526
EPISODE = 'native-40526-1bec95182886'
OLD_GAME = {'pid': 15512, 'creation_filetime': 134368811928524228}


def require(ok, message):
    if not ok:
        raise ValueError('checkpoint6322 cold denied: ' + message)


def exact(ref, expected, *, limit=262144, json_value=True):
    require((ref.get('bytes'), ref.get('sha256')) == expected, 'different finite input pin')
    with Path(ref['path']).open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) == expected[0] <= limit and hashlib.sha256(raw).hexdigest() == expected[1],
            'closed bounded source changed: ' + str(ref['path']))
    return json.loads(raw) if json_value else raw


def project_saved_frontier(admission, *, checkpoint_saved):
    """Reconstruct a source-bound saved seed, never claim an old full snapshot."""
    values = {key: exact(admission[key], PINS[key]) for key in (
        'original_state', 'original_governance', 'rollback_frontier',
        'save_response', 'saved_semantic_response')}
    old, gov, frontier = (values[k] for k in ('original_state', 'original_governance', 'rollback_frontier'))
    row = values['save_response']; semantic = values['saved_semantic_response']
    checkpoint = row['result']['structured_content']['checkpoint']
    turn = frontier['saved_turn_body']; saved = frontier['cumulative_SAVE_event_body']
    require(frontier.get('machine_id') == MACHINE and frontier['save_response'] == admission['save_response']
        and frontier['saved_semantic_response'] == admission['saved_semantic_response']
        and saved['checkpoint'] == checkpoint == old['actual_saved_checkpoint']
        and checkpoint['sha256'] == SAVE_SHA and checkpoint['size'] == 95611139
        and checkpoint['date_raw'] == 53202384 and checkpoint['history_index'] == 2056
        and checkpoint['episode_character_id'] == ACTOR and checkpoint['episode_run_id'] == EPISODE,
        'actual checkpoint/6321/6322/closed-state tuple differs')
    require(row.get('client_error') is None and row['result'].get('is_error') is False
        and row['request']['sequence'] == 6322 and row['request']['tool'] == 'ck3_save_checkpoint'
        and semantic.get('client_error') is None and semantic['result'].get('is_error') is False
        and semantic['request']['sequence'] == 6321
        and semantic['request']['tool'] == 'ck3_take_semantic_snapshot_private_v1', 'original completed tools differ')
    require(old['completed_cycles'] == gov['completed_cycles'] == 3037 and old['start_date_raw'] == 53144328
        and old['before']['date_raw'] == 53202696 and turn['global_turn'] == saved['global_turn'] == 3023
        and turn['after']['date_raw'] == checkpoint['date_raw']
        and turn['after']['actor_character_id'] == ACTOR and turn['after']['episode_run_id'] == EPISODE
        and all(old.get(k) is None for k in ('pending_cycle', 'pending_checkpoint', 'terminal',
            'pending_natural_succession', 'pending_unsafe_route_halt')),
        'clean current/saved frontier differs')
    require(gov['state'] == {'council_pending': None, 'construction_actions': {}, 'prisoner_release_pending': None}
        and gov['pending_cycle'] is None and gov['pending_focus'] is None,
        'cannot carry a future or unknown governance obligation into an older SAVE')
    tail = frontier['post_SAVE_tail']
    require([item['global_turn'] for item in tail] == list(range(3024, 3038))
        and tail[-1]['cumulative_observation_counts'] == old['counts']
        and frontier['historical_post_SAVE_days'] == 13 and frontier['historical_post_SAVE_settled_cycles'] == 14,
        'complete original post-SAVE historical tail required')
    for item in tail:
        # Exact input SHA above binds the individual original rows, including the
        # two old clock holds. No old action is supplied to an execution method.
        exact(item['source'], (item['source']['bytes'], item['source']['sha256']))
    seed = copy.deepcopy(old)
    seed['completed_cycles'] = 3023
    seed['before'] = copy.deepcopy(turn['after'])
    seed['before_metrics_response'] = turn['after_metrics_response']
    seed['before_source_kind'] = 'checkpoint6322_original_settled_metrics'
    seed['counts'] = copy.deepcopy(turn['cumulative_observation_counts'])
    require(seed['counts']['checkpoint_saved'] == 34, 'saved-turn checkpoint count differs')
    seed['counts']['checkpoint_saved'] += 1
    seed['actual_saved_checkpoint'] = copy.deepcopy(checkpoint)
    seed['actual_saved_checkpoint_source'] = {k: saved[k] for k in ('global_turn', 'semantic_response', 'save_response')}
    # War regime from the future cache is deliberately unknown until new actual
    # observations. The checkpoint clock remains the real original SAVE date.
    seed['checkpoint_calendar_v1'] = {'last_saved_date_raw': checkpoint['date_raw'],
        'actor_character_id': ACTOR, 'episode_run_id': EPISODE, 'war_ids': None}
    checkpoint_saved(seed, checkpoint)
    seed.pop('checkpoint_last_decision', None)
    seed['checkpoint6322_rollback'] = {'machine_id': MACHINE,
        'source_frontier': admission['rollback_frontier'], 'original_live_state': admission['original_state'],
        'saved_cycles': 3023, 'saved_date_raw': 53202384, 'historical_later_cycles': 3037,
        'historical_later_date_raw': 53202696, 'rolled_back_cycles': 14, 'rolled_back_game_days': 13,
        'old_full_snapshot_claimed': False, 'original_history_truncated': False,
        'old_action_replayed': False, 'new_cycle_credit': 0}
    projected_gov = copy.deepcopy(gov)
    projected_gov['completed_cycles'] = 3023
    return seed, projected_gov


def validate_rollback(admission, seed, governance, *, checkpoint_saved):
    expected_seed, expected_governance = project_saved_frontier(admission, checkpoint_saved=checkpoint_saved)
    require(seed == expected_seed and governance == expected_governance,
        'seed/governance must exactly equal the finite source reconstruction')


def validate_abnormal_closure(close):
    """Accept only this real forced-old-Game / failed-publisher closure tuple."""
    display = exact(close['abnormal_display_closure'], PINS['abnormal_display_closure'])
    supervisor = exact(close['abnormal_supervisor_closure'], PINS['abnormal_supervisor_closure'])
    require(display['machine_id'] == supervisor['machine_id'] == MACHINE
        and all(close['old_Game'][k] == value for k, value in OLD_GAME.items()), 'old physical Game differs')
    for package in (display, supervisor):
        for ref in package['source_refs']:
            if ref.get('exists') is not False:
                exact(ref, (ref['bytes'], ref['sha256']), json_value=False)
    values = supervisor['source_values']; game = values['ROOT-ACTUAL-GAME-EXIT-C11.json']
    require(game['kernel_signaled'] is True and game['exit_code'] == 1
        and game['forced_owned_job_cleanup'] is True
        and all(game[k] == value for k, value in OLD_GAME.items()), 'actual original Game exit1 required')
    closed = values['ROOT-FRESH-SUPERVISOR-CLOSED-C11.json']
    require(closed['cleanup_classification'] == 'FORCED_OWNED_GAME_CLEANUP'
        and closed['owned_cleanup']['cleanup_proven'] is True
        and closed['owned_cleanup']['tree_gone'] is True
        and 'Resource deadlock avoided' in closed['keeper']['failure']
        and closed['keeper']['last_sequence'] == 7227, 'original keeper cleanup chain differs')
    pub = display['projection']['publisher_closed']; cleanup = display['projection']['recording_cleanup']
    require(pub['publisher']['pid'] == 18096 and pub['publisher']['creation_filetime'] == 134368813345350079
        and pub['normal_STOP_observed'] is False and pub['kernel_exit_not_self_observable'] is True
        and pub['first_error']['type'] == 'PermissionError'
        and display['original_publisher_owner_session_exit_code'] == 1
        and cleanup['inputs_unbound'] is True and cleanup['engine_close']['actual_exit_code'] == 0
        and cleanup['engine_close']['normal_exit_proven'] is True
        and display['new_recorder_retained_kernel_exit_code'] == 0,
        'exact abnormal publisher/normal recording cleanup evidence differs')
    require(close['checkpoint']['sha256'] == SAVE_SHA and close['checkpoint']['history_index'] == 2056
        and close['checkpoint']['date_raw'] == 53202384, 'different checkpoint in finite closure')
    observed = {Path(ref['path']).name: ref for ref in close['sidecars']}
    for name, expected in SIDECARS.items():
        require(name in observed, 'retained historical sidecar missing: ' + name)
        exact(observed[name], expected)
    return {'status': 'EXACT6322_ABNORMAL_CLOSURE_SOURCE_BOUND',
        'publisher_child_numeric_exit_code': None, 'publisher_normal_STOP': False,
        'publisher_owner_exit_code': 1, 'Game_exit_code': 1, 'recording_engine_exit_code': 0,
        'future_material_or_old_action_credit': 0}
