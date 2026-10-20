"""One owned-item action plus independent native intent post-read; no retry."""
from __future__ import annotations
from collections.abc import Mapping
import threading
import uuid
from . import faith_observers_private_transport_v1 as R
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1, private_g2_query_metadata_v1
from .nonwar_private_build import private_native_provenance
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

PERMISSION = 'allow_private_player_artifact_personal_use_actions'
SUBMIT = 'submit-player-artifact-personal-use-v1-private'
POST = 'query-player-artifact-personal-use-action-post-v1-private'
DOMAIN = 'player_artifact_personal_use_action_v1'
KEY = 'player_artifact_personal_use_action'
_LOCK = threading.Lock()


def _state(driver):
    # Synchronization only. The native process-life ledger remains authoritative.
    with _LOCK:
        if not hasattr(driver, '_artifact_personal_use_client_pending_v1'):
            driver._artifact_personal_use_client_pending_v1 = {}
        return driver._artifact_personal_use_client_pending_v1


def _frame(driver, expected_revision):
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError('Personal-item actions and their post observer are independently default OFF')
    R.integer(expected_revision, 'public revision', 1, 2**64-1)
    before = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
    binding = R.owner(before)
    actor = before.get('played_character', {})
    R.need(before.get('revision') == expected_revision and before.get('paused') is True and
           before.get('map_ready') is True and actor.get('alive') is True, 'Action requires current living paused player')
    R.integer(before.get('native_revision'), 'native revision', 1, 2**64-1)
    R.integer(before.get('date_raw'), 'actual native date', 0)
    R.reference(actor.get('character_id'), 'actor')
    return before, binding, (binding[1], actor['character_id'])


def _item(value, snapshot, artifact_id, *, historical=False):
    # A post's before is the actual native ledger's original observation, not a
    # newly synthesized positive DTO. Only its historical date can differ.
    context = snapshot
    if historical:
        R.need(type(value) is dict, 'Original intent before is absent')
        R.integer(value.get('date_raw'), 'original before date')
        R.need(value['date_raw'] <= snapshot['date_raw'], 'Original intent is dated after current post')
        context = {**snapshot, 'date_raw': value['date_raw']}
    return R.normalize_player_artifact_personal_use_v1(value, snapshot=context, artifact_id=artifact_id)


def normalize_artifact_personal_use_action_v1(value, *, snapshot, artifact_id,
        post, expected_intent_sequence=None, submitted=None):
    r = R.shape(value, '''schema game_version executable_sha256 read_only available unavailable_reason
        played_character_id artifact_id desired_equipped expected_slot_index expected_replacing_artifact_id
        intent_sequence intent_found invoked once_intent_consumed dispatch_call_returned needs_recovery
        desired_inventory_state_observed status before_native_revision before_connection_generation before_game_pid
        after_native_revision after_connection_generation after_game_pid before after business_outcome_observed
        actor_aggregate_observed personal_net_effect_attributed total_payment_observed automatic_retry''', 'personal-item action')
    R.need(r['schema'] == 'ck3_12004_player_artifact_personal_use_action_v1' and
        require_exact_native_build(r['game_version'], r['executable_sha256']) == CK3_12004,
        'Personal-item action schema/build differs')
    R.availability(r, 'personal-item action')
    R.need(r['read_only'] is post, 'Action/post read-only role differs')
    R.reference(r['played_character_id'], 'action actor'); R.reference(r['artifact_id'], 'action artifact')
    R.need(r['played_character_id'] == snapshot['played_character']['character_id'] and
        r['artifact_id'] == artifact_id, 'Action crossed current actor/full artifact identity')
    R.boolean(r['desired_equipped'], 'original desired equipment')
    R.integer(r['expected_slot_index'], 'original expected slot', 0, 63)
    R.reference(r['expected_replacing_artifact_id'], 'original replacement', nullable=True)
    R.need(r['desired_equipped'] or r['expected_replacing_artifact_id'] is None, 'Unequip has no replacement item')
    R.integer(r['intent_sequence'], 'native original intent sequence', 0, 2**64-1)
    for field in ('intent_found', 'invoked', 'once_intent_consumed', 'dispatch_call_returned', 'needs_recovery',
                  'desired_inventory_state_observed'):
        R.boolean(r[field], field)
    for field in ('business_outcome_observed', 'actor_aggregate_observed', 'personal_net_effect_attributed',
                  'total_payment_observed', 'automatic_retry'):
        R.need(r[field] is False, 'Action invented aggregate/payment/business credit or automatic retry: '+field)
    R.failure(r['status'], 'action status')
    R.need(not r['intent_found'] or r['intent_sequence'] > 0, 'Found native intent has no actual sequence')
    R.need(not r['once_intent_consumed'] or r['intent_found'], 'Consumed action lacks its retained native intent')
    R.need(not r['invoked'] or r['once_intent_consumed'], 'Invocation lacks native once claim')
    R.need(not r['dispatch_call_returned'] or r['invoked'], 'Callback return lacks invocation')
    historically_resolved = post and r['status'] == 'intent_previously_resolved_current_state_not_observed'
    if r['once_intent_consumed'] and not r['desired_inventory_state_observed'] and not historically_resolved:
        R.need(r['needs_recovery'] is True, 'Unresolved consumed intent cannot be cleared')
    current = R.owner(snapshot)
    before, after = r['before'], r['after']
    for prefix, item in (('before', before), ('after', after)):
        for field, maximum in (('native_revision',2**64-1), ('connection_generation',2**64-1), ('game_pid',2**32-1)):
            R.integer(r[prefix+'_'+field], prefix+' '+field, 0 if item is None else 1, maximum)
        if item is None:
            R.need(all(r[prefix+'_'+field] == 0 for field in ('native_revision','connection_generation','game_pid')),
                'Missing item observation has invented native frame metadata')
        else:
            _item(item, snapshot, artifact_id, historical=prefix == 'before' and post)
            R.need(r[prefix+'_game_pid'] == current[1], 'Original/current item belongs to another process')
    if before is not None and not post:
        R.need(r['before_native_revision'] == snapshot['native_revision'] and
            r['before_connection_generation'] == current[2], 'Submit before crossed request frame')
    if r['once_intent_consumed'] or r['invoked']:
        R.need(before is not None and before['available'] and before['inventory_artifact'] and
            before['inventory_view_visible'] and before['native_equipped_observed'] and
            before['equipped'] is not r['desired_equipped'], 'Consumed action lacks its actual original leaf admission')
        if r['desired_equipped']:
            R.need(before['can_equip_in_effective_slot'] is True and before['effective_slot_index'] == r['expected_slot_index'] and
                before['replacing_artifact_id'] == r['expected_replacing_artifact_id'], 'Invoked equip contradicts actual slot/replacement/permission')
        else:
            R.need(before['equipped_slot_index'] == r['expected_slot_index'] and before['can_unequip'] is True and
                before['slots'][r['expected_slot_index']]['personal'] is True, 'Invoked unequip contradicts actual membership/permission')
    if after is not None:
        R.need(post and r['after_native_revision'] == snapshot['native_revision'] and
            r['after_connection_generation'] == current[2], 'Post after crossed current request frame')
    if not post:
        R.need(after is None and r['desired_inventory_state_observed'] is False, 'Submit ACK cannot resolve desired inventory')
        for field in ('desired_equipped','expected_slot_index','expected_replacing_artifact_id'):
            R.need(r[field] == submitted[field] and type(r[field]) is type(submitted[field]), 'Submit changed original intent: '+field)
    else:
        R.need(r['intent_found'] is True and r['intent_sequence'] == expected_intent_sequence,
            'Post must find the exact original native intent; not-found has no body')
        R.need(r['status'] in {'intent_pending_or_unknown','desired_inventory_state_observed',
            'intent_previously_resolved_current_state_not_observed'}, 'Post status differs')
        R.need((r['status'] == 'desired_inventory_state_observed') is r['desired_inventory_state_observed'],
            'Post status cannot substitute for native independent evidence')
        R.need(r['needs_recovery'] is (r['status'] == 'intent_pending_or_unknown'), 'Post current proof/historical ledger status differs')
        if historically_resolved:
            R.need(r['available'] and r['once_intent_consumed'] and after is not None,
                'Historical resolution cannot replace an invalid current frame or a missing fresh read')
    if r['desired_inventory_state_observed']:
        R.need(post and r['available'] and r['once_intent_consumed'] and r['invoked'] and not r['needs_recovery'] and
            before is not None and after is not None and before['available'] and after['available'] and
            before['equipped'] is not r['desired_equipped'] and after['equipped'] is r['desired_equipped'] and
            after['native_equipped_observed'] is True and after['capture_epoch'] > before['capture_epoch'] and
            r['before_game_pid'] == r['after_game_pid'] and
            r['before_connection_generation'] == r['after_connection_generation'],
            'Desired state lacks the actual independent later native observation')
        if r['desired_equipped']:
            R.need(after['equipped_slot_index'] == r['expected_slot_index'], 'Equipped target slot differs')
            replaced = r['expected_replacing_artifact_id']
            if replaced is not None:
                R.need(replaced in after['owned_ids'] and all(slot['artifact_id'] != replaced for slot in after['slots']),
                    'Replaced artifact ownership/equipment does not match native postcondition')
    return r


def _exchange(driver, before, binding, *, post, fields, artifact_id, submitted=None, expected_intent_sequence=None):
    step = POST if post else SUBMIT
    request_id = 'artifact-personal-once-' + uuid.uuid4().hex
    request = {'type':'execute_step','protocol_version':1,'request_id':request_id,'step':step,
        'expected_revision':before['native_revision'],'expected_snapshot_revision':before['native_revision'],
        'expected_date_raw':before['date_raw'],'expected_actor_character_id':before['played_character']['character_id'],
        'expected_game_pid':binding[1],'expected_connection_generation':binding[2],**fields}
    driver.endpoint.send(request)
    packet = driver.state.wait_for_command_result(request_id, 30.0)
    try:
        R.need(isinstance(packet,Mapping) and packet.get('type') == 'command_result' and
            type(packet.get('protocol_version')) is int and packet['protocol_version'] == 1 and
            packet.get('request_id') == request_id and packet.get('ok') is True,
            'Original artifact command RED/unknown; retain native intent and never replay')
        envelope = packet.get('result')
        R.need(type(envelope) is dict and envelope.get('step') == step and envelope.get('accepted') is True and
            envelope.get('private_build') is True and envelope.get('read_only') is post and
            envelope.get('advertised') is False and envelope.get('domain_key') == DOMAIN and
            require_exact_native_backend(envelope.get('game_version'),envelope.get('executable_sha256'),
                envelope.get('backend_id'),suffix='player-artifact-personal-use-action-v1-private') == CK3_12004 and
            type(envelope.get('snapshot_revision')) is int and envelope['snapshot_revision'] == before['native_revision'] and
            type(envelope.get('date_raw')) is int and envelope['date_raw'] == before['date_raw'], 'Action envelope crossed request/build/frame')
        value = normalize_artifact_personal_use_action_v1(envelope.get(KEY),snapshot=before,artifact_id=artifact_id,
            post=post,submitted=submitted,expected_intent_sequence=expected_intent_sequence)
        R.need(envelope.get('status') == ('observed' if value['available'] else 'unavailable'), 'Action availability status differs')
        after = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        after_binding = R.owner(after)
        if post:
            R.need(after_binding == binding, 'Read-only post crossed its current frame')
        else:
            R.need(after_binding[1:] == binding[1:] and after['played_character']['character_id'] == before['played_character']['character_id'] and
                after.get('paused') is True and after.get('map_ready') is True and after['played_character'].get('alive') is True and
                after['date_raw'] >= before['date_raw'], 'Submit lost original current process/actor')
    except (ValueError,KeyError,TypeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value,**private_native_provenance(before),**private_g2_query_metadata_v1(before),
        'snapshot_revision':before['native_revision'],'backend_id':envelope['backend_id'],
        'domain_key':DOMAIN,'advertised':False,'post_snapshot_id':after.get('snapshot_id')}


def submit_player_artifact_personal_use_private_v1(driver, *, expected_revision, artifact_id,
        desired_equipped, expected_slot_index, expected_replacing_artifact_id=None, policy_positive=False):
    R.reference(artifact_id,'artifact');R.boolean(desired_equipped,'desired_equipped')
    R.integer(expected_slot_index,'expected slot',0,63)
    R.reference(expected_replacing_artifact_id,'expected replacement',nullable=True)
    R.need(policy_positive is True, 'Positive policy required for one actual artifact mutation')
    R.need(desired_equipped or expected_replacing_artifact_id is None, 'Unequip requires null replacement')
    before,binding,key = _frame(driver,expected_revision)
    pending = _state(driver)
    intent = {'artifact_id':artifact_id,'desired_equipped':desired_equipped,'expected_slot_index':expected_slot_index,
              'expected_replacing_artifact_id':expected_replacing_artifact_id,'intent_sequence':None}
    with _LOCK:
        if key in pending: raise BridgeUnavailableError('Prior unresolved personal-item command is retained; use exact native intent post, never replay')
        pending[key] = intent  # Unknown submissions stay latched before original send.
    fields = {**{k:intent[k] for k in ('artifact_id','desired_equipped','expected_slot_index')},
        'policy_positive':True,'expected_replacing_empty':expected_replacing_artifact_id is None}
    if expected_replacing_artifact_id is not None:fields['expected_replacing_artifact_id']=expected_replacing_artifact_id
    value = _exchange(driver,before,binding,post=False,fields=fields,artifact_id=artifact_id,submitted=intent)
    with _LOCK:
        if pending.get(key) is intent:
            intent['intent_sequence'] = value['intent_sequence'] or None
            if not value['once_intent_consumed'] and not value['invoked'] and not value['needs_recovery']:
                del pending[key]  # Independently returned pre-invocation rejection only.
        value['client_replay_blocked'] = key in pending
    return value


def query_player_artifact_personal_use_action_post_private_v1(driver, *, expected_revision, artifact_id, expected_intent_sequence):
    R.reference(artifact_id,'artifact');R.integer(expected_intent_sequence,'actual original intent sequence',1,2**64-1)
    before,binding,key = _frame(driver,expected_revision)
    pending = _state(driver)
    with _LOCK:
        intent = pending.get(key)
        if intent is not None:
            R.need(intent['artifact_id'] == artifact_id and intent['intent_sequence'] in (None,expected_intent_sequence),
                'Post does not match this client original unresolved artifact/sequence')
    value = _exchange(driver,before,binding,post=True,artifact_id=artifact_id,
        fields={'artifact_id':artifact_id,'expected_intent_sequence':expected_intent_sequence},expected_intent_sequence=expected_intent_sequence)
    if intent is not None:
        for field in ('desired_equipped','expected_slot_index','expected_replacing_artifact_id'):
            R.need(value[field] == intent[field] and type(value[field]) is type(intent[field]), 'Post changed retained client intent')
    if value['desired_inventory_state_observed']:
        with _LOCK:
            if pending.get(key) is intent and intent is not None:del pending[key]
    with _LOCK:
        value['client_replay_blocked'] = key in pending
    return value
