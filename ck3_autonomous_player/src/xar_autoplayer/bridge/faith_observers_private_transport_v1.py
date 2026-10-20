"""Exact4 personal-item and Faith GHW observations; no gameplay command."""
from __future__ import annotations
from collections.abc import Mapping
import math
import re
import uuid
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_metadata_v1, private_g2_query_snapshot_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .timeline_blocker_private_transport import _binding
from .version_identity import CK3_12004, require_exact_native_build, require_exact_native_backend

ARTIFACT_STEP = 'query-player-artifact-personal-use-v1'
GHW_STEP = 'query-player-ghw-permissions-v1-private'
ARTIFACT_PERMISSION = 'allow_private_player_artifact_personal_use_query'
GHW_PERMISSION = 'allow_private_player_ghw_permissions_query'
VARIABLES = (('variable_ghw_unlocked', 'religion'), ('variable_first_ghw_cooldown', 'religion'),
             ('variable_ghw_cooldown', 'faith'), ('variable_ghw_global_unlocking_cooldown', 'global'))
UNIT = 'signed32_native_scalar_counter_calendar_unqualified'


def need(value, message):
    if not value:
        raise ValueError(message)


def shape(value, keys, field):
    need(type(value) is dict and set(value) == set(keys.split()), 'Native observer shape differs: ' + field)
    return value


def integer(value, field, lo=-(2**31), hi=2**31-1, nullable=False):
    if value is None and nullable: return value
    need(type(value) is int and lo <= value <= hi, 'Native observer integer differs: ' + field)
    return value


def boolean(value, field, nullable=False):
    need(type(value) is bool or nullable and value is None, 'Native observer bool differs: ' + field)
    return value


def reference(value, field, nullable=False, raw=False):
    return integer(value, field, 0, 2**32-1 if raw else 2**32-2, nullable)


def failure(value, field):
    need(type(value) is str and bool(value) and len(value) <= 256, 'Native observer failure differs: ' + field)


def availability(value, field):
    boolean(value['available'], field)
    need(value['unavailable_reason'] is None if value['available'] else
         type(value['unavailable_reason']) is str and bool(value['unavailable_reason']),
         'Native observer availability reason differs: ' + field)


def owner(snapshot):
    need(private_native_build_identity(snapshot) == CK3_12004, 'Observer requires exact4 snapshot')
    diagnostics = snapshot.get('diagnostics')
    need(isinstance(diagnostics, Mapping), 'Native owner diagnostics absent')
    hello = diagnostics.get('hello')
    need(isinstance(hello, Mapping), 'Native owner hello absent')
    pid, generation = diagnostics.get('bridge_pid'), diagnostics.get('connection_generation')
    integer(pid, 'game pid', 1, 2**32-1); integer(generation, 'generation', 1, 2**64-1)
    need(hello.get('pid') == pid and hello.get('connection_generation') == generation
         and hello.get('ck3_build_match') is True and
         require_exact_native_build(hello.get('expected_ck3_version'), hello.get('expected_ck3_sha256')) == CK3_12004,
         'Observer hello owner/build differs')
    return (_binding(snapshot), pid, generation, CK3_12004)


def frame_fields(result, snapshot):
    need(require_exact_native_build(result['game_version'], result['executable_sha256']) == CK3_12004,
         'Observer body requires exact4 build')
    integer(result['capture_epoch'], 'capture epoch', 0, 2**64-1)
    integer(result['date_raw'], 'date')
    reference(result['played_character_id'], 'actor')
    need(result['date_raw'] == snapshot.get('date_raw') and
         result['played_character_id'] == snapshot.get('played_character', {}).get('character_id'),
         'Observer body crossed current actor/date')
    boolean(result['loaded_source_pins_verified'], 'source pins')
    if result['available']: need(result['capture_epoch'] > 0, 'Available observer has no pump epoch')


def normalize_player_artifact_personal_use_v1(value, *, snapshot, artifact_id):
    reference(artifact_id, 'requested artifact')
    r = shape(value, '''schema game_version executable_sha256 available unavailable_reason
        loaded_source_pins_verified capture_epoch date_raw played_character_id requested_artifact_id
        owned_ids slots personally_owned inventory_artifact equipped native_equipped_observed
        inventory_view_available inventory_view_visible equipped_slot_index effective_slot_index
        replacing_artifact_id can_equip_in_effective_slot can_unequip item_modifier_definition
        modifier_description modifier_names_bound actor_aggregate_observed personal_net_effect_attributed
        total_payment_observed action_ready business_outcome_observed read_only''', 'artifact')
    need(r['schema'] == 'ck3_12004_player_artifact_personal_use_v1', 'Artifact schema differs')
    availability(r, 'artifact'); frame_fields(r, snapshot)
    need(type(r['requested_artifact_id']) is int and r['requested_artifact_id'] == artifact_id,
         'Artifact request full identity differs')
    for key in ('modifier_names_bound', 'actor_aggregate_observed', 'personal_net_effect_attributed',
                'total_payment_observed', 'action_ready', 'business_outcome_observed'):
        need(r[key] is False, 'Item observation invented aggregate/action credit: ' + key)
    need(r['read_only'] is True, 'Artifact query must remain read-only')
    boolean(r['native_equipped_observed'], 'native equipped observed')
    for key in ('personally_owned', 'inventory_artifact', 'equipped', 'inventory_view_available', 'inventory_view_visible'):
        boolean(r[key], key, nullable=not r['available'])
    for key in ('can_equip_in_effective_slot', 'can_unequip'): boolean(r[key], key, nullable=True)
    for key in ('equipped_slot_index', 'effective_slot_index'): integer(r[key], key, 0, 63, True)
    reference(r['replacing_artifact_id'], 'replacing artifact', nullable=True)
    definition = shape(r['item_modifier_definition'], 'available entries', 'item definition')
    description = shape(r['modifier_description'], 'available text', 'item description')
    boolean(definition['available'], 'definition availability'); boolean(description['available'], 'description availability')
    if definition['available']:
        need(type(definition['entries']) is list and len(definition['entries']) <= 128, 'Item definition list differs')
        for raw in definition['entries']:
            item = shape(raw, 'key_raw_u16 definition_value_raw_q64', 'modifier entry')
            integer(item['key_raw_u16'], 'modifier key', 0, 65535)
            integer(item['definition_value_raw_q64'], 'modifier raw value', -(2**63), 2**63-1)
    else: need(definition['entries'] is None, 'Unknown definition must remain null')
    if description['available']:
        need(type(description['text']) is str and len(description['text']) <= 8192, 'Modifier text differs')
    else: need(description['text'] is None, 'Unknown modifier text must remain null')
    if r['available']:
        need(r['loaded_source_pins_verified'] is True and r['personally_owned'] is True,
             'Available artifact requires actual source pins and current ownership')
        need(type(r['owned_ids']) is list and len(r['owned_ids']) <= 64, 'Owned IDs list differs')
        for item in r['owned_ids']: reference(item, 'owned full ID')
        need(len(set(r['owned_ids'])) == len(r['owned_ids']) and r['owned_ids'].count(artifact_id) == 1,
             'Requested artifact is not uniquely in current owned inventory')
        need(type(r['slots']) is list and len(r['slots']) <= 64, 'Artifact slots differ')
        indices = []
        for raw in r['slots']:
            slot = shape(raw, 'index key artifact_id personal', 'artifact slot')
            indices.append(integer(slot['index'], 'slot index', 0, 63))
            reference(slot['artifact_id'], 'slot full ID', nullable=True); boolean(slot['personal'], 'slot personal')
            need(type(slot['key']) is str and re.fullmatch('[a-z0-9_]{1,63}', slot['key']), 'Slot key differs')
        need(len(indices) == len(set(indices)), 'Duplicate native slot index')
        need(indices == list(range(len(indices))), 'Native slot ordinal order differs')
        need(all(slot['artifact_id'] is None or slot['artifact_id'] in r['owned_ids'] for slot in r['slots']),
             'Slot contains an artifact outside current owned inventory')
        matches = [slot for slot in r['slots'] if slot['artifact_id'] == artifact_id]
        need(len(matches) <= 1 and r['equipped'] is bool(matches) and
             r['equipped_slot_index'] == (matches[0]['index'] if matches else None), 'Equipped slot/current item disagree')
        if r['native_equipped_observed']:
            need(type(r['can_unequip']) is bool and r['can_unequip'] is r['equipped'], 'Native equipped predicate differs')
        else: need(r['can_unequip'] is None, 'Unequip predicate was not observed')
        need(not r['inventory_view_visible'] or r['inventory_view_available'], 'Visible inventory view is unavailable')
        effective = r['effective_slot_index']
        if effective is None:
            need(r['replacing_artifact_id'] is None and r['can_equip_in_effective_slot'] is None,
                 'Effective-slot terms lack a real effective slot')
        else:
            need(r['inventory_view_available'] and effective < len(r['slots']) and
                 r['replacing_artifact_id'] == r['slots'][effective]['artifact_id'], 'Effective slot/replacement differs')
            if r['can_equip_in_effective_slot'] is not None:
                need(r['inventory_artifact'] and r['slots'][effective]['personal'], 'Equip predicate lacks personal inventory slot')
    else:
        for key in ('owned_ids', 'slots', 'personally_owned', 'inventory_artifact', 'equipped',
                    'inventory_view_available', 'inventory_view_visible', 'equipped_slot_index',
                    'effective_slot_index', 'replacing_artifact_id', 'can_equip_in_effective_slot', 'can_unequip'):
            need(r[key] is None, 'Unavailable artifact leaked current state: ' + key)
        need(r['native_equipped_observed'] is False and definition['available'] is False and
             description['available'] is False, 'Unavailable artifact leaked positive definition/equipment')
    return r


def normalize_player_ghw_permissions_v1(value, *, snapshot):
    r = shape(value, '''schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw
        played_character_id faith_id religion_id loaded_source_pins_verified frame_verified variables object_links
        launch_permission_inferred raw_pointer_fields_persisted read_only''', 'GHW')
    need(r['schema'] == 'ck3_12004_player_ghw_permissions_v1', 'GHW schema differs')
    availability(r, 'GHW'); frame_fields(r, snapshot)
    reference(r['faith_id'], 'faith raw ID', True, True); reference(r['religion_id'], 'religion raw ID', True, True)
    boolean(r['frame_verified'], 'GHW frame')
    need(r['launch_permission_inferred'] is False and r['raw_pointer_fields_persisted'] is False and
         r['read_only'] is True, 'GHW query invented launch/pointer/action credit')
    v = shape(r['variables'], 'available_any all_fields_observed frame_verified stable_two_pass failure remaining_unit fields', 'variables')
    for key in ('available_any', 'all_fields_observed', 'frame_verified', 'stable_two_pass'): boolean(v[key], 'variables.'+key)
    failure(v['failure'], 'variables.failure')
    need(v['remaining_unit'] == UNIT, 'Native counter cannot become a calendar duration')
    need(type(v['fields']) is list and len(v['fields']) == 4, 'Four fixed GHW variables required')
    observed = []
    nullable = ('present', 'timed', 'expiry_raw', 'current_counter_raw', 'remaining_raw',
                'value_kind_raw', 'numeric_value_raw', 'expiry_date_raw')
    for raw, (key, scope) in zip(v['fields'], VARIABLES):
        field = shape(raw, 'key scope read_available present timed expiry_raw current_counter_raw remaining_raw value_kind_raw numeric_value_raw expiry_date_raw failure', key)
        need(field['key'] == key and field['scope'] == scope, 'GHW variable key/scope/order differs')
        observed.append(boolean(field['read_available'], key+'.read_available'))
        failure(field['failure'], key+'.failure')
        boolean(field['present'], key+'.present', nullable=not field['read_available'])
        boolean(field['timed'], key+'.timed', nullable=True)
        for name in ('expiry_raw', 'current_counter_raw', 'remaining_raw'): integer(field[name], key+'.'+name, nullable=True)
        integer(field['value_kind_raw'], key+'.kind', 0, 65535, True)
        integer(field['numeric_value_raw'], key+'.value', -(2**63), 2**63-1, True)
        need(field['expiry_date_raw'] is None, 'Unqualified counter cannot be a calendar deadline')
        if not field['read_available']:
            need(all(field[name] is None for name in nullable) and field['failure'] != 'none',
                 'Unavailable variable leaked or fabricated a current fact')
        else:
            need(field['failure'] == 'none', 'Observed variable retains a failure')
            integer(field['current_counter_raw'], key+'.current counter')
            if not field['present']:
                need(field['timed'] is False and field['remaining_raw'] == -1 and
                     all(field[name] is None for name in ('expiry_raw', 'value_kind_raw', 'numeric_value_raw')),
                     'Absent variable invented timed or value facts')
            else:
                expiry = integer(field['expiry_raw'], key+'.expiry')
                kind = integer(field['value_kind_raw'], key+'.kind', 0, 65535)
                expected_remaining = ((expiry-field['current_counter_raw']+2**31) % 2**32)-2**31 if expiry >= 0 else -1
                need(field['timed'] is (expiry >= 0) and field['remaining_raw'] == expected_remaining,
                     'Variable timedness/counter/remaining contradict native signed32 helper')
                if kind == 1: integer(field['numeric_value_raw'], key+'.numeric', -(2**63), 2**63-1)
                else: need(field['numeric_value_raw'] is None, 'Non-numeric variable leaked a payload value')
    need(v['available_any'] == any(observed) and v['all_fields_observed'] == all(observed),
         'Variable availability summary differs')
    links = shape(r['object_links'], 'available stable_two_pass ghw war failure ghw_reference_full_id war_reference_full_id faith_has_offensive_ghw has_war_started', 'object links')
    boolean(links['available'], 'object.available'); boolean(links['stable_two_pass'], 'object.stable')
    failure(links['failure'], 'object.failure')
    need(links['ghw'] in {'unknown', 'absent', 'present'} and links['war'] in {'unknown', 'absent', 'present'},
         'GHW object state differs')
    for key in ('ghw_reference_full_id', 'war_reference_full_id'): reference(links[key], key, True, True)
    for key in ('faith_has_offensive_ghw', 'has_war_started'): boolean(links[key], key, nullable=True)
    if links['ghw'] == 'present': reference(links['ghw_reference_full_id'], 'resolved GHW ID')
    if links['war'] == 'present': reference(links['war_reference_full_id'], 'resolved war ID')
    ghw_ref, war_ref = links['ghw_reference_full_id'], links['war_reference_full_id']
    if ghw_ref == 0xFFFFFFFF: need(links['ghw'] == 'absent', 'Native null GHW reference must be classified absent')
    if war_ref == 0xFFFFFFFF: need(links['war'] == 'absent', 'Native null war reference must be classified absent')
    if ghw_ref is None:
        need(links['faith_has_offensive_ghw'] is None, 'Unobserved GHW link gained a predicate')
    else:
        need(links['faith_has_offensive_ghw'] is (ghw_ref != 0xFFFFFFFF), 'GHW link predicate differs from raw reference')
    if war_ref is None:
        need(links['has_war_started'] is None, 'Unobserved war link gained a predicate')
    else:
        need(links['has_war_started'] is (war_ref != 0xFFFFFFFF) and links['ghw'] == 'present',
             'War link predicate/source differs from raw reference')
    if links['available']:
        need(links['stable_two_pass'] is True and links['failure'] == 'none' and
             links['ghw'] != 'unknown' and links['war'] != 'unknown', 'Available GHW object must be fully observed/stable')
    else:
        need(links['failure'] != 'none', 'Unavailable GHW object needs its actual failure')
        if ghw_ref is not None or war_ref is not None or links['ghw'] == 'present':
            need(links['stable_two_pass'] is True, 'Partial object facts lack stable observations')
    if links['ghw'] == 'absent':
        need(links['available'] and links['war'] == 'absent' and ghw_ref == 0xFFFFFFFF and war_ref is None and
             links['faith_has_offensive_ghw'] is False and links['has_war_started'] is None,
             'Absent GHW link contradicts reachable-war facts')
    elif links['ghw'] == 'unknown':
        need(links['war'] == 'unknown' and war_ref is None, 'Unknown GHW cannot resolve its war link')
    else:
        need(links['faith_has_offensive_ghw'] is True, 'Resolved GHW lacks non-null Faith link')
        if links['war'] == 'absent':
            need(links['available'] and war_ref == 0xFFFFFFFF and links['has_war_started'] is False,
                 'Absent linked war contradicts native null reference')
        if links['war'] == 'present': need(links['available'], 'Resolved war cannot be an incomplete object observation')
    if r['available']:
        reference(r['faith_id'], 'current Faith full ID'); reference(r['religion_id'], 'current Religion full ID')
        need(r['loaded_source_pins_verified'] is True and r['frame_verified'] is True and
             v['frame_verified'] is True and v['stable_two_pass'] is True,
             'Available GHW observation lacks the stable current frame')
    else:
        need(r['frame_verified'] is False and r['faith_id'] is None and r['religion_id'] is None and
             v['frame_verified'] is False and v['stable_two_pass'] is False and links['stable_two_pass'] is False and
             not any(observed) and not links['available'] and links['ghw'] == links['war'] == 'unknown' and
             all(links[key] is None for key in ('ghw_reference_full_id', 'war_reference_full_id',
                 'faith_has_offensive_ghw', 'has_war_started')), 'Outer frame failure leaked stale GHW facts')
    return r


def _query(driver, *, permission, step, domain, result_key, suffix, expected_revision,
           artifact_id=None, timeout_seconds=30.0):
    if getattr(driver, permission, False) is not True: raise UnsupportedStepError('Native observer is default OFF: '+step)
    integer(expected_revision, 'public revision', 1, 2**64-1)
    need(type(timeout_seconds) in (int, float) and math.isfinite(timeout_seconds) and 0 < timeout_seconds <= 300,
         'Native observer requires a finite bounded timeout')
    before = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
    binding = owner(before)
    actor = before.get('played_character', {})
    need(before.get('revision') == expected_revision and before.get('paused') is True and
         before.get('map_ready') is True and actor.get('alive') is True, 'Observer requires current living paused player')
    native = integer(before.get('native_revision'), 'native revision', 1, 2**64-1)
    fields = {'expected_date_raw': integer(before.get('date_raw'), 'date', 0),
              'expected_actor_character_id': reference(actor.get('character_id'), 'actor'),
              'expected_game_pid': binding[1], 'expected_connection_generation': binding[2]}
    if artifact_id is not None: fields['artifact_id'] = reference(artifact_id, 'artifact')
    request_id = 'g2-read-' + uuid.uuid4().hex
    driver.endpoint.send({'type': 'execute_step', 'protocol_version': 1, 'request_id': request_id,
        'step': step, 'expected_revision': native, 'expected_snapshot_revision': native, **fields})
    packet = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    try:
        need(isinstance(packet, Mapping) and packet.get('type') == 'command_result' and
             type(packet.get('protocol_version')) is int and packet['protocol_version'] == 1 and
             packet.get('request_id') == request_id and packet.get('ok') is True, 'Native observer returned RED or foreign request')
        envelope = packet.get('result')
        need(type(envelope) is dict and envelope.get('step') == step and envelope.get('accepted') is True and
             envelope.get('private_build') is True and envelope.get('read_only') is True and
             envelope.get('advertised') is False, 'Native observer envelope differs')
        need(require_exact_native_backend(envelope.get('game_version'), envelope.get('executable_sha256'),
             envelope.get('backend_id'), suffix=suffix) == CK3_12004 and envelope.get('domain_key') == domain and
             type(envelope.get('snapshot_revision')) is int and envelope['snapshot_revision'] == native and
             type(envelope.get('date_raw')) is int and envelope['date_raw'] == before['date_raw'],
             'Native observer envelope crossed build/frame/domain')
        if artifact_id is not None:
            value = normalize_player_artifact_personal_use_v1(envelope.get(result_key), snapshot=before, artifact_id=artifact_id)
        else:
            value = normalize_player_ghw_permissions_v1(envelope.get(result_key), snapshot=before)
        need(envelope.get('status') == ('observed' if value['available'] else 'unavailable'), 'Native observer status differs')
        after = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        need(owner(after) == binding, 'Native observer crossed process/generation/build/current frame')
    except (ValueError, KeyError, TypeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            'snapshot_revision': native, 'backend_id': envelope['backend_id'], 'domain_key': domain,
            'status': envelope['status'], 'advertised': False}


def query_player_artifact_personal_use_private_v1(driver, *, expected_revision, artifact_id):
    reference(artifact_id, 'requested artifact')
    return _query(driver, permission=ARTIFACT_PERMISSION, step=ARTIFACT_STEP,
        domain='player_artifact_personal_use_v1', result_key='player_artifact_personal_use',
        suffix='player-artifact-personal-use-v1', expected_revision=expected_revision, artifact_id=artifact_id)


def query_player_ghw_permissions_private_v1(driver, *, expected_revision):
    return _query(driver, permission=GHW_PERMISSION, step=GHW_STEP,
        domain='player_ghw_permissions', result_key='player_ghw_permissions',
        suffix='player-ghw-permissions-v1-private', expected_revision=expected_revision)
