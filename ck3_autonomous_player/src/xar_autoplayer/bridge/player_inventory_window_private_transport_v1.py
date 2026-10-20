"""Source-bound normal HUD inventory open and exact independent intent post."""
from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
import re
import threading
import uuid
from . import faith_observers_private_transport_v1 as R
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1, private_g2_query_metadata_v1
from .nonwar_private_build import private_native_provenance
from .normal_exit_source_inventory_v1 import verify_source_inventory_v1
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

PERMISSION='allow_private_player_inventory_window_open'
QUERY='query-player-inventory-window-v1-private'
OPEN='open-player-inventory-window-v1-private'
POST='query-player-inventory-window-open-post-v1-private'
DOMAIN='player_inventory_window_v1'
KEY='player_inventory_window'
_LOCK=threading.Lock()
_STATES=('window_present','root_present','native_visible','effective_visible','current_player_selected')


def _source_inventory(driver):
    # Same actual managed-source verifier and running/launch choice as normal
    # exit _prepare. This does not enable any normal-exit operation or capability.
    profile=getattr(driver,'normal_exit_managed_profile',None)
    reference=profile.get('normal_exit_source_inventory') if type(profile) is dict else None
    if type(reference) is not dict:
        raise UnsupportedStepError('Inventory opening requires the existing actual managed-source inventory')
    try:
        evidence=profile.get('evidence_directory')
        allocated=isinstance(evidence,str) and any((Path(evidence)/name).exists() for name in ('frozen-argv.json','ready-context.json'))
        sources=verify_source_inventory_v1(reference,profile,input_phase='running' if allocated else 'launch')
        digest=sources['source_inventory_sha256']
        R.need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,
            'Managed-source verifier did not return an exact lowercase SHA256')
        return digest
    except (OSError,ValueError,TypeError,KeyError) as error:
        raise UnsupportedStepError('Inventory managed-source verification failed: '+str(error)) from error


def _frame(driver,expected_revision):
    if getattr(driver,PERMISSION,False) is not True:
        raise UnsupportedStepError('Inventory query/open/post permission is independently default OFF')
    R.integer(expected_revision,'public revision',1,2**64-1)
    digest=_source_inventory(driver)
    before=private_g2_query_snapshot_v1(driver,include_native_command_history=False)
    binding=R.owner(before);actor=before.get('played_character',{})
    R.need(before.get('revision')==expected_revision and before.get('paused') is True and
        before.get('map_ready') is True and actor.get('alive') is True,'Inventory operation needs current living paused player')
    R.integer(before.get('native_revision'),'native revision',1,2**64-1)
    R.integer(before.get('date_raw'),'actual native date',0)
    R.integer(actor.get('character_id'),'current full actor',1,2**32-2)
    return before,binding,(binding[1],actor['character_id']),digest


def _pending(driver):
    with _LOCK:
        if not hasattr(driver,'_player_inventory_window_client_pending_v1'):
            driver._player_inventory_window_client_pending_v1={}
        return driver._player_inventory_window_client_pending_v1


def _view(value,*,snapshot,binding,historical=False):
    v=R.shape(value,'''available native_revision capture_epoch date_raw game_pid connection_generation
        played_character_id selected_character_id window_present root_present native_visible effective_visible current_player_selected''','inventory VIEW')
    R.boolean(v['available'],'VIEW availability')
    R.integer(v['native_revision'],'VIEW native revision',0,2**64-1)
    R.integer(v['capture_epoch'],'VIEW capture epoch',0,2**64-1)
    R.integer(v['date_raw'],'VIEW date',0)
    R.integer(v['game_pid'],'VIEW actual PID',1,2**32-1)
    R.integer(v['connection_generation'],'VIEW generation',1,2**64-1)
    R.integer(v['played_character_id'],'VIEW full actor',1,2**32-2)
    R.reference(v['selected_character_id'],'VIEW full selected actor',nullable=True)
    R.need(v['game_pid']==binding[1] and v['played_character_id']==snapshot['played_character']['character_id'],
        'Inventory VIEW belongs to another process/player')
    if not historical:
        R.need(v['native_revision']==snapshot['native_revision'] and v['date_raw']==snapshot['date_raw'] and
            v['connection_generation']==binding[2],'Inventory current VIEW crossed the actual request frame')
    if v['available']:
        R.need(v['native_revision']>0 and v['capture_epoch']>0,'Available VIEW lacks actual revision/capture epoch')
        for field in _STATES:R.boolean(v[field],field)
        R.need(v['window_present'] is True and v['current_player_selected'] is (v['selected_character_id']==v['played_character_id']),
            'Available inventory VIEW contradicts its actual view/full selected actor')
        if not v['root_present']:
            R.need(v['native_visible'] is False and v['effective_visible'] is False,'Missing native root cannot prove inventory visibility')
    else:
        R.need(v['selected_character_id'] is None and all(v[key] is None for key in _STATES),
            'Unavailable inventory VIEW leaked positive/negative state facts')
    return v


def normalize_player_inventory_window_v1(value,*,snapshot,operation,expected_intent_sequence=None):
    r=R.shape(value,'''schema game_version executable_sha256 operation read_only available unavailable_reason
        loaded_code_pins_verified loaded_gui_sources_verified current intent_sequence intent_found once_intent_consumed
        invoked call_returned needs_recovery desired_window_observed status before after artifact_equipped_observed
        actor_aggregate_observed personal_net_effect_attributed business_outcome_observed automatic_retry''','inventory result')
    R.need(r['schema']=='ck3_12004_player_inventory_window_v1' and
        require_exact_native_build(r['game_version'],r['executable_sha256'])==CK3_12004,'Inventory schema/build differs')
    R.availability(r,'inventory result')
    R.need(r['operation']==operation and r['read_only'] is (operation!='open'),'Inventory operation/read-only role differs')
    binding=R.owner(snapshot)
    for key in ('loaded_code_pins_verified','loaded_gui_sources_verified','intent_found','once_intent_consumed',
                'invoked','call_returned','needs_recovery','desired_window_observed'):R.boolean(r[key],key)
    for key in ('artifact_equipped_observed','actor_aggregate_observed','personal_net_effect_attributed','business_outcome_observed','automatic_retry'):
        R.need(r[key] is False,'Inventory opener invented equip/aggregate/business/retry credit: '+key)
    R.failure(r['status'],'inventory status')
    R.integer(r['intent_sequence'],'actual original inventory intent',0,2**64-1)
    R.need(r['intent_found'] is (r['intent_sequence']>0),'Inventory native intent presence/sequence differ')
    R.need(not r['once_intent_consumed'] or r['intent_found'],'Consumed inventory intent was not retained')
    R.need(not r['invoked'] or r['once_intent_consumed'],'Inventory invocation has no native once claim')
    R.need(not r['call_returned'] or r['invoked'],'Inventory call return lacks invocation')
    current=_view(r['current'],snapshot=snapshot,binding=binding)
    if r['available']:
        R.need(current['available'] and r['loaded_code_pins_verified'] and r['loaded_gui_sources_verified'],
            'Available inventory result lacks current read/code/selected GUI source admission')
    else:
        R.need(current['available'] is False,'Outer inventory admission failure retained current facts')
    before,after=r['before'],r['after']
    if before is not None:_view(before,snapshot=snapshot,binding=binding,historical=operation!='open')
    if after is not None:
        _view(after,snapshot=snapshot,binding=binding)
        R.need(operation=='post' and after==current,'Independent post after must be the actual current VIEW')
    if operation=='query':
        R.need(after is None and r['desired_window_observed'] is False,'Ordinary query cannot resolve original opening')
        R.need(r['status']==('inventory_window_observed' if r['available'] else 'inventory_window_unavailable'),
            'Inventory query status differs')
    elif operation=='open':
        R.need(after is None and r['desired_window_observed'] is False,'Open ACK cannot prove actual desired window')
        R.need(r['intent_found'] is r['once_intent_consumed'],'Open may retain only this ticket actual once claim')
        if r['once_intent_consumed']:R.need(r['needs_recovery'] is True,'Submitted inventory claim cannot self-resolve')
    else:
        R.need(r['intent_found'] is True and r['intent_sequence']==expected_intent_sequence,
            'Post must find the exact original actual native intent; not-found has no body')
        statuses={'inventory_intent_pending_or_unknown','inventory_window_desired_observed',
            'inventory_intent_previously_resolved_current_window_not_observed'}
        R.need(r['status'] in statuses,'Inventory post status differs')
        R.need(r['desired_window_observed'] is (r['status']=='inventory_window_desired_observed') and
            r['needs_recovery'] is (r['status']=='inventory_intent_pending_or_unknown'),
            'Inventory post current proof and historical ledger status differ')
        if r['status']=='inventory_intent_previously_resolved_current_window_not_observed':
            R.need(r['available'] and r['once_intent_consumed'] and after is not None,
                'Historical inventory resolution cannot replace an invalid fresh owner frame')
    if r['once_intent_consumed']:
        R.need(before is not None and before['available'],'Consumed inventory intent lacks actual original available VIEW')
        R.need(not (before['root_present'] and before['native_visible'] and before['effective_visible'] and before['current_player_selected']),
            'Native opener cannot claim an already visible current-player inventory')
    if r['desired_window_observed']:
        R.need(operation=='post' and r['available'] and r['once_intent_consumed'] and before is not None and after is not None and
            before['available'] and after['available'] and after['capture_epoch']>before['capture_epoch'] and
            after['connection_generation']==before['connection_generation'] and after['game_pid']==before['game_pid'] and
            after['played_character_id']==before['played_character_id'] and after['native_revision']>=before['native_revision'] and
            after['date_raw']>=before['date_raw'] and all(after[key] is True for key in _STATES),
            'Desired inventory window lacks actual independent later current-player root/visibility proof')
    return r


def _exchange(driver,before,binding,digest,*,operation,expected_intent_sequence=None):
    step={'query':QUERY,'open':OPEN,'post':POST}[operation]
    request_id='inventory-window-'+operation+'-'+uuid.uuid4().hex
    request={'type':'execute_step','protocol_version':1,'request_id':request_id,'step':step,
        'expected_revision':before['native_revision'],'expected_snapshot_revision':before['native_revision'],
        'expected_date_raw':before['date_raw'],'expected_actor_character_id':before['played_character']['character_id'],
        'expected_game_pid':binding[1],'expected_connection_generation':binding[2],'source_inventory_sha256':digest}
    if operation=='post':request['expected_intent_sequence']=expected_intent_sequence
    driver.endpoint.send(request)
    packet=driver.state.wait_for_command_result(request_id,30.0)
    try:
        R.need(isinstance(packet,Mapping) and packet.get('type')=='command_result' and
            type(packet.get('protocol_version')) is int and packet['protocol_version']==1 and
            packet.get('request_id')==request_id and packet.get('ok') is True,
            'Inventory response RED/unknown; retain original native intent, never replay')
        e=packet.get('result')
        R.need(type(e) is dict and e.get('step')==step and e.get('accepted') is True and e.get('private_build') is True and
            e.get('advertised') is False and e.get('read_only') is (operation!='open') and e.get('domain_key')==DOMAIN and
            require_exact_native_backend(e.get('game_version'),e.get('executable_sha256'),e.get('backend_id'),
                suffix='player-inventory-window-v1-private')==CK3_12004 and
            type(e.get('snapshot_revision')) is int and e['snapshot_revision']==before['native_revision'] and
            type(e.get('date_raw')) is int and e['date_raw']==before['date_raw'] and
            type(e.get('game_pid')) is int and e['game_pid']==binding[1] and
            type(e.get('connection_generation')) is int and e['connection_generation']==binding[2],
            'Inventory response crossed actual build/process/generation/request frame')
        value=normalize_player_inventory_window_v1(e.get(KEY),snapshot=before,operation=operation,
            expected_intent_sequence=expected_intent_sequence)
        R.need(e.get('status')==('observed' if value['available'] else 'unavailable'),'Inventory envelope availability differs')
        after=private_g2_query_snapshot_v1(driver,include_native_command_history=False)
        after_binding=R.owner(after)
        if operation!='open':R.need(after_binding==binding,'Inventory readonly operation crossed its exact current frame')
        else:
            R.need(after_binding[1:]==binding[1:] and after['played_character']['character_id']==before['played_character']['character_id'] and
                after.get('paused') is True and after.get('map_ready') is True and after['played_character'].get('alive') is True and
                after['date_raw']>=before['date_raw'],'Inventory opening lost original process/player frame')
    except (ValueError,KeyError,TypeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value,**private_native_provenance(before),**private_g2_query_metadata_v1(before),
        'backend_id':e['backend_id'],'domain_key':DOMAIN,'snapshot_revision':before['native_revision'],
        'client_source_inventory_sha256':digest,'advertised':False,'post_snapshot_id':after.get('snapshot_id')}


def query_player_inventory_window_private_v1(driver,*,expected_revision):
    before,binding,key,digest=_frame(driver,expected_revision)
    value=_exchange(driver,before,binding,digest,operation='query')
    pending=_pending(driver)
    with _LOCK:
        intent=pending.get(key)
        if intent is not None and intent['intent_sequence'] is None and value['intent_found']:
            intent['intent_sequence']=value['intent_sequence']  # Actual latest native sequence only; no resolution.
        value['client_replay_blocked']=key in pending
    return value


def open_player_inventory_window_private_v1(driver,*,expected_revision):
    before,binding,key,digest=_frame(driver,expected_revision)
    pending=_pending(driver);intent={'intent_sequence':None}
    with _LOCK:
        if key in getattr(driver,'_player_inventory_window_close_client_pending_v1',{}):
            raise BridgeUnavailableError('Prior inventory closing remains unknown; resolve its exact Close intent before opening')
        if key in pending:raise BridgeUnavailableError('Prior inventory opening remains unknown; use actual original-intent post, never replay')
        pending[key]=intent
    value=_exchange(driver,before,binding,digest,operation='open')
    with _LOCK:
        if pending.get(key) is intent:
            intent['intent_sequence']=value['intent_sequence'] or None
            if (not value['once_intent_consumed'] and not value['invoked'] and not value['needs_recovery'] and
                    value['status']!='inventory_pending_or_once_ledger_rejected'):
                del pending[key]
        value['client_replay_blocked']=key in pending
    return value


def query_player_inventory_window_open_post_private_v1(driver,*,expected_revision,expected_intent_sequence):
    R.integer(expected_intent_sequence,'actual original inventory intent',1,2**64-1)
    before,binding,key,digest=_frame(driver,expected_revision)
    pending=_pending(driver)
    with _LOCK:
        intent=pending.get(key)
        if intent is not None:R.need(intent['intent_sequence'] in (None,expected_intent_sequence),'Post changed retained actual native inventory intent')
    value=_exchange(driver,before,binding,digest,operation='post',expected_intent_sequence=expected_intent_sequence)
    with _LOCK:
        if value['desired_window_observed'] and intent is not None and pending.get(key) is intent:del pending[key]
        value['client_replay_blocked']=key in pending
    return value
