"""One actor-backed native KnightEffectiveness observation; no site attribution."""
from __future__ import annotations
from collections.abc import Mapping
import uuid
from . import faith_observers_private_transport_v1 as R
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1, private_g2_query_metadata_v1
from .nonwar_private_build import private_native_provenance
from .version_identity import CK3_12004, require_exact_native_build

PERMISSION = 'allow_private_character_knight_effectiveness_query'
STEP = 'query-character-knight-effectiveness-v1-private'
DOMAIN = 'character_knight_effectiveness_v1'
BODY_FIELDS = frozenset('''schema available unavailable_reason read_only snapshot_revision date_raw
    played_character_id character_id rite_id faith_id knight_effectiveness_raw actual_knight_effectiveness_breakdown
    raw_scale two_pass_stable own_actor_context_verified callback_provenance modifier_cache_refreshed
    cache_generation_time_known site_attribution_observed selected_site_contribution_raw gameplay_command_submitted
    raw_pointer_fields_persisted script_cache_rng_effects game_version executable_sha256'''.split())


def normalize_character_knight_effectiveness_v1(value, *, snapshot, character_id):
    R.reference(character_id, 'requested full actor')
    r = R.shape(value, ' '.join(BODY_FIELDS), 'actor knight effectiveness')
    R.need(r['schema'] == 'ck3_12004_character_knight_effectiveness_v1' and
        require_exact_native_build(r['game_version'], r['executable_sha256']) == CK3_12004,
        'KnightEffectiveness schema/build differs')
    R.availability(r, 'knight effectiveness')
    R.need(r['read_only'] is True, 'KnightEffectiveness observer submitted gameplay')
    R.integer(r['snapshot_revision'], 'actual native revision', 1, 2**64-1)
    R.integer(r['date_raw'], 'actual native date')
    R.integer(r['played_character_id'], 'actual played full actor', 1, 2**32-2)
    R.reference(r['character_id'], 'target full actor')
    R.need(r['snapshot_revision'] == snapshot['native_revision'] and r['date_raw'] == snapshot['date_raw'] and
        r['played_character_id'] == snapshot['played_character']['character_id'] and r['character_id'] == character_id,
        'KnightEffectiveness crossed the requested target/current frame')
    for field in ('modifier_cache_refreshed', 'cache_generation_time_known', 'site_attribution_observed',
                  'gameplay_command_submitted', 'raw_pointer_fields_persisted'):
        R.need(r[field] is False, 'KnightEffectiveness invented refresh/attribution/action/pointer credit: ' + field)
    R.need(type(r['raw_scale']) is int and r['raw_scale'] == 100000 and
        r['selected_site_contribution_raw'] is None and r['script_cache_rng_effects'] == 'unknown',
        'KnightEffectiveness raw scale/attribution/cache contract differs')
    R.boolean(r['two_pass_stable'], 'actor two-pass stability')
    R.boolean(r['own_actor_context_verified'], 'actual owned actor context')
    nullable = ('rite_id', 'faith_id', 'knight_effectiveness_raw', 'actual_knight_effectiveness_breakdown')
    if r['available']:
        R.need(r['two_pass_stable'] is True and r['own_actor_context_verified'] is True and
            r['callback_provenance'] == 'exact4_native',
            'Available KnightEffectiveness lacks the actual stable actor-backed native context; shared100% fallback is unqualified')
        R.reference(r['rite_id'], 'target Rite'); R.reference(r['faith_id'], 'target Faith')
        R.integer(r['knight_effectiveness_raw'], 'native signed q64 effectiveness', -(2**63), 2**63-1)
        text = r['actual_knight_effectiveness_breakdown']
        R.need(type(text) is str and len(text.encode('utf-8')) <= 32768,
            'Original native KnightEffectiveness text exceeds its UTF8 contract')
    else:
        R.need(r['two_pass_stable'] is False and r['own_actor_context_verified'] is False and
            r['callback_provenance'] == 'unavailable' and all(r[field] is None for field in nullable),
            'Unavailable KnightEffectiveness leaked actor values or default fallback/text')
    return r


def query_character_knight_effectiveness_private_v1(driver, *, expected_revision, character_id):
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError('Character KnightEffectiveness observation is independently default OFF')
    R.reference(character_id, 'requested full actor')
    R.integer(expected_revision, 'public revision', 1, 2**64-1)
    before = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
    binding = R.owner(before); actor = before.get('played_character', {})
    R.integer(before.get('revision'), 'actual public revision', 1, 2**64-1)
    R.need(before['revision'] == expected_revision and before.get('paused') is True and before.get('map_ready') is True and
        actor.get('alive') is True, 'KnightEffectiveness needs the actual current living paused player frame')
    native = R.integer(before.get('native_revision'), 'actual native revision', 1, 2**64-1)
    fields = {'expected_date_raw': R.integer(before.get('date_raw'), 'actual native date', 0),
        'expected_actor_character_id': R.integer(actor.get('character_id'), 'actual played actor', 1, 2**32-2),
        'expected_game_pid': binding[1], 'expected_connection_generation': binding[2], 'character_id': character_id}
    request_id = 'actor-knight-read-' + uuid.uuid4().hex
    driver.endpoint.send({'type': 'execute_step', 'protocol_version': 1, 'request_id': request_id, 'step': STEP,
        'expected_revision': native, 'expected_snapshot_revision': native, **fields})
    packet = driver.state.wait_for_command_result(request_id, 30.0)
    try:
        R.need(isinstance(packet, Mapping) and packet.get('type') == 'command_result' and
            type(packet.get('protocol_version')) is int and packet['protocol_version'] == 1 and
            packet.get('request_id') == request_id and packet.get('ok') is True,
            'KnightEffectiveness native observation is RED/unknown or belongs to another request')
        envelope = packet.get('result')
        R.need(type(envelope) is dict and envelope.get('step') == STEP and envelope.get('accepted') is True and
            envelope.get('private_build') is True and envelope.get('read_only') is True and envelope.get('advertised') is False and
            envelope.get('backend_id') == 'native-headless' and envelope.get('domain_key') == DOMAIN and
            type(envelope.get('game_pid')) is int and envelope['game_pid'] == binding[1] and
            type(envelope.get('connection_generation')) is int and envelope['connection_generation'] == binding[2] and
            require_exact_native_build(envelope.get('game_version'), envelope.get('executable_sha256')) == CK3_12004 and
            type(envelope.get('snapshot_revision')) is int and envelope['snapshot_revision'] == native and
            type(envelope.get('date_raw')) is int and envelope['date_raw'] == before['date_raw'],
            'KnightEffectiveness response crossed the actual build/process/generation/request frame')
        value = normalize_character_knight_effectiveness_v1(envelope.get(DOMAIN), snapshot=before, character_id=character_id)
        R.need(envelope.get('status') == ('available' if value['available'] else 'unavailable'),
            'KnightEffectiveness native availability status differs')
        after = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        R.need(R.owner(after) == binding, 'KnightEffectiveness crossed the actual current actor/process/generation/frame')
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        'backend_id': 'native-headless', 'domain_key': DOMAIN, 'status': envelope['status'], 'advertised': False}
