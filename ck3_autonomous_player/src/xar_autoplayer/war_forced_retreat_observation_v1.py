"""Recognize an already active Native retreat, without ordering a retreat."""


def native_forced_retreat_observation_v1(snapshot, armies):
    if not isinstance(snapshot, dict) or not isinstance(armies, list) or not armies:
        return None
    actor = snapshot.get('played_character')
    hint = snapshot.get('top_exclusive_modal_choice_hint')
    revision = snapshot.get('native_revision')
    if not (snapshot.get('backend_id') == 'native-headless'
            and snapshot.get('source') == 'injected-dll-named-pipe'
            and snapshot.get('paused') is True and snapshot.get('map_ready') is True
            and type(revision) is int and revision > 0
            and snapshot.get('snapshot_id') == 'native:' + str(revision)
            and type(snapshot.get('revision')) is int and snapshot['revision'] > 0
            and type(snapshot.get('date_raw')) is int
            and isinstance(snapshot.get('episode_run_id'), str) and snapshot['episode_run_id']
            and isinstance(actor, dict) and actor.get('alive') is True
            and type(actor.get('character_id')) is int
            and 'active_event' in snapshot and snapshot['active_event'] is None
            and 'pending_character_interaction' in snapshot and snapshot['pending_character_interaction'] is None
            and not (isinstance(hint, dict) and hint.get('status') == 'present')):
        return None
    ids = []
    for army in armies:
        if not isinstance(army, dict):
            return None
        route = army.get('route_province_ids')
        if not (type(army.get('army_id')) is int and army['army_id'] >= 0
                and army.get('source') == 'native'
                and army.get('owner_character_id') == actor['character_id']
                and army.get('controllable') is True
                and army.get('army_state') == 'retreating' and army.get('army_state_code') == 6
                and army.get('retreating') is True and army.get('in_combat') is False
                and type(army.get('current_province_id')) is int and army['current_province_id'] > 0
                and army.get('move_target_observable') is True
                and type(army.get('move_target_province_id')) is int and army['move_target_province_id'] > 0
                and army.get('route_read_status') == 'complete_nonempty'
                and isinstance(route, list) and route
                and all(type(p) is int and p > 0 for p in route)
                and route[-1] == army['move_target_province_id']):
            return None
        ids.append(army['army_id'])
    if len(set(ids)) != len(ids):
        return None
    published = snapshot.get('player_armies')
    if (not isinstance(published, list) or
            {a.get('army_id') for a in published if isinstance(a, dict) and a.get('controllable') is True} != set(ids)):
        return None
    return {'schema':'xar.ck3.existing-native-forced-retreat/v1',
        'army_ids': sorted(ids), 'source_snapshot_id':snapshot['snapshot_id'],
        'source_native_revision':revision, 'source_date_raw':snapshot.get('date_raw'),
        'existing_native_retreat_only':True, 'new_retreat_order':False,
        'contact_free_proven':False, 'attack_authorized':False,
        'arrival_or_battle_success_inferred':False}
