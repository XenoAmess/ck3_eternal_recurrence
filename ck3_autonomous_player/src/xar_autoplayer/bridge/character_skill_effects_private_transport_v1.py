"""Read one exact full-ID actor's cached six skills and original native text."""
from __future__ import annotations
from collections.abc import Mapping
import uuid
from . import faith_observers_private_transport_v1 as R
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1, private_g2_query_metadata_v1
from .nonwar_private_build import private_native_provenance
from .version_identity import CK3_12004, require_exact_native_build

PERMISSION = 'allow_private_character_skill_effects_query'
STEP = 'query-character-skill-effects-v1-private'
DOMAIN = 'character_skill_effects_v1'
SKILLS = ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess')


def skill_index(value):
    R.need(type(value) is str and value in SKILLS, 'Skill must be one of the six finite native names')
    return SKILLS.index(value)


def normalize_character_skill_effects_v1(value, *, snapshot, character_id, skill):
    enum = skill_index(skill)
    r = R.shape(value, '''schema available unavailable_reason read_only snapshot_revision date_raw
        played_character_id character_id requested_skill requested_skill_enum rite_id faith_id
        current_skill_points effective_devotion_level devotion_total_raw actual_skill_breakdown
        raw_scale skill_scale two_pass_stable callback_provenance skill_cache_refreshed
        cache_generation_time_known site_attribution_observed selected_site_contribution_raw
        gameplay_command_submitted raw_pointer_fields_persisted script_cache_rng_effects game_version executable_sha256''', 'actor skill effects')
    R.need(r['schema'] == 'ck3_12004_character_skill_effects_v1' and
        require_exact_native_build(r['game_version'], r['executable_sha256']) == CK3_12004,
        'Actor observer schema/build differs')
    R.availability(r, 'actor skill effects')
    R.need(r['read_only'] is True, 'Actor observer submitted gameplay')
    R.integer(r['snapshot_revision'], 'actor native revision', 1, 2**64-1)
    R.integer(r['date_raw'], 'actor current date')
    R.reference(r['played_character_id'], 'current actor');R.reference(r['character_id'], 'target actor')
    R.integer(r['requested_skill_enum'], 'skill enum', 0, 5)
    R.need(r['snapshot_revision'] == snapshot['native_revision'] and r['date_raw'] == snapshot['date_raw'] and
        r['played_character_id'] == snapshot['played_character']['character_id'] and r['character_id'] == character_id and
        r['requested_skill'] == skill and type(r['requested_skill']) is str and r['requested_skill_enum'] == enum,
        'Actor observer crossed requested target/skill/current frame')
    for name in ('skill_cache_refreshed', 'cache_generation_time_known', 'site_attribution_observed',
                 'gameplay_command_submitted', 'raw_pointer_fields_persisted'):
        R.need(r[name] is False, 'Actor observer invented refresh/attribution/action/pointer fact: '+name)
    R.need(type(r['raw_scale']) is int and r['raw_scale'] == 100000 and
        type(r['skill_scale']) is int and r['skill_scale'] == 1 and
        r['selected_site_contribution_raw'] is None and r['script_cache_rng_effects'] == 'unknown',
        'Actor observer invented numeric attribution or native cache semantics')
    R.boolean(r['two_pass_stable'], 'two-pass actor stability')
    optional = ('rite_id','faith_id','current_skill_points','effective_devotion_level','devotion_total_raw','actual_skill_breakdown')
    if r['available']:
        R.need(r['two_pass_stable'] is True and r['callback_provenance'] == 'exact4_native',
            'Available actor observer lacks exact stable production native source')
        R.reference(r['rite_id'], 'target Rite');R.reference(r['faith_id'], 'target Faith')
        skills = R.shape(r['current_skill_points'], ' '.join(SKILLS), 'native six cached skills')
        for key in SKILLS:R.integer(skills[key], 'cached '+key, -(2**31), 2**31-1)
        R.integer(r['effective_devotion_level'], 'own effective devotion', -(2**31), 2**31-1)
        R.integer(r['devotion_total_raw'], 'cumulative devotion raw q64', -(2**63), 2**63-1)
        R.need(type(r['actual_skill_breakdown']) is str and len(r['actual_skill_breakdown'].encode('utf-8')) <= 32768,
            'Original SkillItem text exceeds its bounded native contract')
    else:
        R.need(r['two_pass_stable'] is False and r['callback_provenance'] == 'unavailable' and
            all(r[field] is None for field in optional), 'Unavailable actor component leaked partial values')
    return r


def query_character_skill_effects_private_v1(driver, *, expected_revision, character_id, skill='diplomacy'):
    R.reference(character_id, 'requested actor');enum = skill_index(skill)
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError('Character skill effects observation is default OFF')
    R.integer(expected_revision, 'public revision', 1, 2**64-1)
    before = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
    binding = R.owner(before)
    actor = before.get('played_character', {})
    R.need(before.get('revision') == expected_revision and before.get('paused') is True and
        before.get('map_ready') is True and actor.get('alive') is True, 'Actor observer requires a current living paused player')
    native = R.integer(before.get('native_revision'), 'native revision', 1, 2**64-1)
    fields = {'expected_date_raw':R.integer(before.get('date_raw'), 'actual native date', 0),
        'expected_actor_character_id':R.reference(actor.get('character_id'), 'current played actor'),
        'expected_game_pid':binding[1], 'expected_connection_generation':binding[2],
        'character_id':character_id, 'skill_key':skill, 'skill_enum':enum}
    request_id = 'actor-skill-read-' + uuid.uuid4().hex
    driver.endpoint.send({'type':'execute_step','protocol_version':1,'request_id':request_id,'step':STEP,
        'expected_revision':native,'expected_snapshot_revision':native,**fields})
    packet = driver.state.wait_for_command_result(request_id, 30.0)
    try:
        R.need(isinstance(packet,Mapping) and packet.get('type') == 'command_result' and
            type(packet.get('protocol_version')) is int and packet['protocol_version'] == 1 and
            packet.get('request_id') == request_id and packet.get('ok') is True, 'Actor observer native command is RED/foreign')
        envelope = packet.get('result')
        R.need(type(envelope) is dict and envelope.get('step') == STEP and envelope.get('accepted') is True and
            envelope.get('private_build') is True and envelope.get('read_only') is True and
            envelope.get('advertised') is False and envelope.get('backend_id') == 'native-headless' and
            envelope.get('domain_key') == DOMAIN and
            type(envelope.get('game_pid')) is int and envelope['game_pid'] == binding[1] and
            type(envelope.get('connection_generation')) is int and envelope['connection_generation'] == binding[2] and
            require_exact_native_build(envelope.get('game_version'),envelope.get('executable_sha256')) == CK3_12004 and
            type(envelope.get('snapshot_revision')) is int and envelope['snapshot_revision'] == native and
            type(envelope.get('date_raw')) is int and envelope['date_raw'] == before['date_raw'],
            'Actor observer envelope crossed exact native build/role/request frame')
        value = normalize_character_skill_effects_v1(envelope.get(DOMAIN),snapshot=before,character_id=character_id,skill=skill)
        R.need(envelope.get('status') == ('available' if value['available'] else 'unavailable'), 'Actor availability status differs')
        after = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        R.need(R.owner(after) == binding, 'Actor observation crossed current process/generation/build/frame')
    except (ValueError,KeyError,TypeError,UnicodeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value,**private_native_provenance(before),**private_g2_query_metadata_v1(before),
        'backend_id':'native-headless','domain_key':DOMAIN,'status':envelope['status'],'advertised':False}
