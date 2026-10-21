from typing import cast
from pointer_read_models import PointerOwnerBinding,JsonObject,object_value,u64
from pointer_read_admission_models import text
"""Explicit ordinary-null ownership for the finite writer observer; no OS/API calls."""
EPISODE_BOUND = 'episode_bound_v1'
ORDINARY = 'native_campaign_character_pointer_read_v1'
SCHEMA = 'xar.maintenance.parent_pointer_read.owner-binding.v2'
CALLSITE_RVA = 0x28F7840

def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError('writer owner binding: ' + message)

def positive(value: object, name: str, limit: int=(1 << 64)) -> int:
    need(type(value) is int and 0 < value < limit, name + ' must be a positive native integer')
    return cast(int,value)

def episode_arguments(mode: str, episode: str | None) -> list[str]:
    need(mode in (EPISODE_BOUND, ORDINARY), 'unknown explicit mode')
    if mode == EPISODE_BOUND:
        need(type(episode) is str and bool(episode.strip()) and
             all(c.isascii() and (c.isalnum() or c in '-_.') for c in episode),
             'legacy episode must remain a real nonempty identifier')
        return ['--expected-episode', cast(str,episode)]
    need(episode is None, 'ordinary-null mode cannot relabel a nonnull episode')
    return ['--owner-binding-mode', ORDINARY]

def qualify(mode: str, episode: str | None, snapshot: JsonObject, journal: JsonObject, leaf: JsonObject, *, expected_game_state: int | None=None,
            expected_local_player_id: int | None=None) -> PointerOwnerBinding | None:
    episode_arguments(mode, episode)
    need(snapshot.get('episode_run_id') == episode, 'original episode differs')
    if mode == EPISODE_BOUND:
        return None
    need(snapshot.get('episode_projection') == 'native_campaign', 'ordinary projection required')
    need(snapshot.get('paused') is True and snapshot.get('map_ready') is True,
         'paused ready frame required')
    actor = object_value(snapshot.get('played_character'),'played character')
    need(actor.get('alive') is True, 'living original actor required')
    s = object_value(journal['current_session'],'session')
    d = object_value(snapshot['diagnostics'],'diagnostics')
    player = positive(snapshot.get('local_player_id'), 'local player', 1 << 32)
    need(player == expected_local_player_id, 'independent local player differs')
    state = positive(s['game_state_identity_witness'], 'GameState', 0x7ffffffff001)
    heartbeat=object_value(d.get('last_heartbeat'),'heartbeat')
    mailbox=object_value(heartbeat.get('main_thread_query_mailbox_v1'),'mailbox')
    need(type(mailbox.get('game_state')) is int and mailbox['game_state'] == state == expected_game_state,
         'independent snapshot/journal GameState differs')
    need(journal['controlled_window_admitted'] is True and s['same_owned_process_no_load_window'] is True
         and s['loaded_game_epoch'] is None and object_value(journal['sampling'],'sampling')['capture_enabled'] is True,
         'actual controlled no-load window required')
    need(d['bridge_pid'] == s['pid'] and type(d['bridge_pid']) is int
         and d['connection_generation'] == s['connection_generation'] and type(d['connection_generation']) is int
         and actor.get('character_id') == s['player_character_full_id'] and type(actor.get('character_id')) is int,
         'original process/generation/actor differs')
    need(snapshot['native_revision'] == s['snapshot_revision'] == leaf['snapshot_revision']
         and snapshot['date_raw'] == leaf['date_raw'] == (u64(s['native_date_raw'],'native date') & 0xffffffff),
         'actual native frame/date differs')
    out = dict(schema=SCHEMA, mode=ORDINARY, episode_projection='native_campaign',
               episode_run_id=None, original_episode_key_present='episode_run_id' in snapshot,
               pid=s['pid'], process_create_time_100ns=s['process_create_time_100ns'],
               connection_generation=s['connection_generation'], player_character_full_id=s['player_character_full_id'],
               local_player_id=player, game_state_identity_witness=state,
               character=leaf['character'], context=object_value(leaf['values'],'values')['context_identity_before'],
               controlled_window_id=s['controlled_window_id'], payment_epoch=object_value(journal['sampling'],'sampling')['epoch'],
               native_revision=leaf['snapshot_revision'], date_raw=leaf['date_raw'],
               absolute_day_raw=s['absolute_day_raw'], callsite_anchor_rva=CALLSITE_RVA)
    return validate(out)

def validate(owner: object) -> PointerOwnerBinding:
    owner=object_value(owner,"owner")
    keys = {'schema','mode','episode_projection','episode_run_id','original_episode_key_present',
            'pid','process_create_time_100ns','connection_generation','player_character_full_id',
            'local_player_id','game_state_identity_witness','character','context','controlled_window_id',
            'payment_epoch','native_revision','date_raw','absolute_day_raw','callsite_anchor_rva'}
    need(type(owner) is dict and set(owner) == keys, 'v2 shape differs')
    need(owner['schema'] == SCHEMA and owner['mode'] == ORDINARY
         and owner['episode_projection'] == 'native_campaign' and owner['episode_run_id'] is None
         and type(owner['original_episode_key_present']) is bool, 'null episode provenance differs')
    for key in keys - {'schema','mode','episode_projection','episode_run_id','original_episode_key_present','date_raw','absolute_day_raw','context'}:
        positive(owner[key], key)
    need(u64(owner['pid'],'pid') < (1 << 32) and u64(owner['player_character_full_id'],'id') < 0xffffffff
         and u64(owner['local_player_id'],'local player') < (1 << 32), 'native identity width differs')
    need(type(owner['date_raw']) is int and 0 <= owner['date_raw'] < 0xffffffff-24
         and type(owner['absolute_day_raw']) is int and 0 <= owner['absolute_day_raw'] < 0xffffffff,
         'native one-day date bounds differ')
    need(owner['callsite_anchor_rva'] == CALLSITE_RVA, 'source callsite anchor differs')
    for key in ('game_state_identity_witness','character','context'):
        need(u64(owner[key],key) <= 0x7ffffffff000, 'invalid native address: '+key)
    need(type(owner['context']) is int and 0<=owner['context']<=0x7ffffffff000,'optional secondary pointer')
    need(u64(owner['character'],'character')%8==0,'aligned Character field')
    return cast(PointerOwnerBinding,owner)

def metadata(owner: PointerOwnerBinding) -> JsonObject:
    validate(owner)
    return dict(owner_binding_schema=SCHEMA, owner_binding_mode=ORDINARY,
                episode_projection='native_campaign', episode_is_null=1, episode_id='',
                original_episode_key_present=int(owner['original_episode_key_present']),
                game_state_identity_witness=owner['game_state_identity_witness'],
                local_player_id=owner['local_player_id'], absolute_day_raw=owner['absolute_day_raw'],
                callsite_anchor_rva=CALLSITE_RVA)

def native_argv_tail(owner: PointerOwnerBinding | None) -> list[str]:
    if owner is None:
        return []
    validate(owner)
    return ['--ordinary-null-owner-binding']
