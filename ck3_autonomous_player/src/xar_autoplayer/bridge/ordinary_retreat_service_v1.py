"""Ordinary battle retreat stages using existing typed readers and one-use order.

Planning reads existing frames and small durable state. Every Native call stays
in the execution phase, after the ordinary decision display/interception hook.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path

from ..environment import write_json_atomic
from ..war_active_retreat_v1 import (
    intent_path, normal_retreat_loss_budget, propose_retreat, submit_once,
    verify_independent_post, verify_terminal_post,
)
from .native_driver import _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES
from .war_contract import is_life_advance_step, parse_battle_decision_epoch_advance_step

PREVIEW = 'ordinary-active-retreat-preview-v1'
ORDER = 'ordinary-active-retreat-order-v1'
POST = 'ordinary-active-retreat-observe-v1'
STEPS = {PREVIEW, ORDER, POST}
FIELD = 'ordinary_active_retreat_v1'
LEDGER = 'ordinary-active-retreat-v1.json'
MAX_BYTES = 256 * 1024


def _frame(snapshot):
    result = {key: snapshot.get(key) for key in (
        'snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')}
    result['connection_generation'] = snapshot.get('diagnostics', {}).get('connection_generation')
    return result


def _read(directory):
    path = directory / LEDGER
    if not path.exists():
        return {'schema': 'ordinary-active-retreat/v1', 'pending': None,
                'preview': None, 'last_attempt': None, 'last_post': None}
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('ordinary retreat state exceeds bounded reader')
    state = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(state, dict) or not {'schema', 'pending', 'preview', 'last_attempt', 'last_post'} <= set(state)
            or state.get('schema') != 'ordinary-active-retreat/v1'
            or state.get('pending') is not None and not isinstance(state['pending'], dict)):
        raise ValueError('ordinary retreat state is malformed; retain unresolved evidence')
    return state


def _write(directory, state):
    state['observed_utc'] = datetime.now(timezone.utc).isoformat()
    if len(json.dumps(state, ensure_ascii=False).encode('utf-8')) > MAX_BYTES:
        raise ValueError('ordinary retreat state exceeds bounded writer')
    write_json_atomic(directory / LEDGER, state)


def _quiet(plan):
    step = plan.get('selected_step')
    return (is_life_advance_step(step)
            or parse_battle_decision_epoch_advance_step(step) is not None)


def _job(plan, kind, snapshot, **fields):
    return {**plan, 'phase': 'native_war_active_retreat_' + kind,
            'selected_step': {'preview': PREVIEW, 'order': ORDER, 'observe': POST}[kind],
            'reason': {'preview': '当前领土防御战处于劣势；下一冻结 tick 兵损超过5%政策预算，先核一跳友军集结路线。',
                       'order': '当帧原生允许撤退且一跳友军路线已核；单次撤退以保留后续防御兵力，追击损失和未来安全仍未知。',
                       'observe': '核上一笔撤退的独立军队状态与原 CombatID；不重复提交。'}[kind],
            FIELD: {'kind': kind, 'source_frame': _frame(snapshot), **fields}}


def plan_ordinary_retreat_v1(driver, plan, *, snapshot, history, bridge_capabilities):
    """Keep mandatory windows, concrete orders and incomplete battle reads first."""
    directory = getattr(driver, 'state_dir', None)
    if not (isinstance(directory, Path) and _quiet(plan)
            and snapshot.get('paused') is True and snapshot.get('map_ready') is True
            and snapshot.get('active_event') is None
            and snapshot.get('pending_character_interaction') is None
            and snapshot.get('one_life_settlement') is None
            and snapshot.get('played_character', {}).get('alive') is True):
        return plan
    try:
        state = _read(directory)
    except (OSError, ValueError) as error:
        return {**plan, FIELD: {'status': 'unavailable', 'reason': str(error)}}
    pending = state['pending']
    if pending is not None:
        if pending.get('episode_run_id') != snapshot.get('episode_run_id'):
            return {**plan, FIELD: {'status': 'prior_episode_intent_retained_no_replay'}}
        if state.get('last_attempt') != {'kind': 'observe', 'frame': _frame(snapshot)}:
            return _job(plan, 'observe', snapshot, intent=pending)
        return {**plan, FIELD: {'status': 'original_unresolved_continue_normal_battle',
                               'last_post': state.get('last_post'), 'replay_allowed': False}}
    if (not _ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES <= set(bridge_capabilities)
            or plan.get('phase') not in {'native_war_global_battle_control_progress',
                                        'native_war_global_battle_decision_epoch',
                                        'native_war_global_battle_terminal_cruise'}):
        return plan
    from ..strategy import _battle_control_turn_state
    from .war_contract import controllable_armies
    control_state = _battle_control_turn_state(history, dict(snapshot),
        controllable_armies(snapshot.get('player_armies', [])))
    if control_state.get('status') != 'ready':
        return plan
    for control in control_state.get('full_frames', []):
        try:
            budget = normal_retreat_loss_budget(snapshot, control)
            if budget['status'] != 'observed':
                continue
            preview = state.get('preview')
            if not isinstance(preview, Mapping) or preview.get('source_binding') != _frame(snapshot):
                preview = None
            decision = propose_retreat(snapshot, control, bridge_capabilities,
                maximum_next_tick_hard_loss_raw=budget['maximum_next_tick_hard_loss_raw'],
                preview=preview)
            args = {'selected_public_cunit_id': control['selected_public_cunit_id'],
                    'expected_combat_id': control['combat_id']}
            # The durable exclusion survives ledger replacement or a lost ACK.
            claim = intent_path(directory, snapshot['episode_run_id'], args)
            if claim.exists():
                return {**plan, FIELD: {'status': 'original_claim_retained_no_replay'}}
            if decision['stage'] == 'order':
                return _job(plan, 'order', snapshot, proposal=decision, loss_budget=budget)
            if (decision['stage'] == 'preview'
                    and state.get('last_attempt') != {'kind': 'preview', 'frame': _frame(snapshot)}):
                return _job(plan, 'preview', snapshot, selected_public_cunit_id=args['selected_public_cunit_id'],
                            target_province_id=decision['target_province_id'], loss_budget=budget)
            plan = {**plan, FIELD: {'status': decision['stage'], 'reason': decision.get('reason'),
                                  'missing': decision.get('missing'), 'loss_budget': budget}}
        except (ValueError, TypeError, KeyError) as error:
            plan = {**plan, FIELD: {'status': 'current_inputs_unavailable', 'reason': str(error)}}
    return plan


def _current(service, planned):
    snapshot = service.snapshot(include_native_command_history=False)
    job = planned['plan'][FIELD]
    if (_frame(snapshot) != job['source_frame'] or snapshot.get('paused') is not True
            or snapshot.get('map_ready') is not True or snapshot.get('active_event') is not None
            or snapshot.get('pending_character_interaction') is not None
            or snapshot.get('one_life_settlement') is not None):
        raise ValueError('ordinary retreat source frame changed; do not submit')
    return snapshot, job


def execute_ordinary_retreat_v1(service, planned):
    """One existing typed operation after the normal before_submit hook."""
    snapshot, job = _current(service, planned)
    directory = service._strategy_state_dir()
    if not isinstance(directory, Path):
        raise ValueError('ordinary retreat requires durable state')
    state = _read(directory)
    kind = job['kind']
    from .relic_action_private_transport import _machine_identity
    machine, reader_sha, policy = _machine_identity(service.driver)
    state.update(machine_id=machine, machine_reader_sha256=reader_sha, storage_policy=policy)
    if kind == 'preview':
        if state['pending'] is not None:
            raise ValueError('original retreat pending intent keeps priority')
        state.update(last_attempt={'kind': kind, 'frame': _frame(snapshot)}, preview=None)
        _write(directory, state)
        try:
            result = service.preview_active_combat_retreat_v1(job['selected_public_cunit_id'],
                job['target_province_id'], expected_revision=snapshot['revision'])
            state['preview'] = result
            _write(directory, state)
        except Exception as error:
            result = {'status': 'preview_unavailable', 'error': f'{type(error).__name__}: {error}',
                      'submit_attempted': False, 'replay_allowed': False}
    elif kind == 'order':
        if state['pending'] is not None:
            raise ValueError('original retreat pending intent must not be resubmitted')
        proposal = job['proposal']
        # Publish pending before the exclusive claim and typed send. Even a
        # crash between those writes leaves observation-only ownership.
        state['pending'] = {key: copy.deepcopy(proposal[key]) for key in (
            'source_binding', 'selected_owner_character_id',
            'affected_public_cunit_ids_in_stored_order',
            'unaffected_same_side_public_cunit_ids_in_stored_order', 'route_province_ids')}
        state['pending'].update(arguments=proposal['arguments'], episode_run_id=snapshot['episode_run_id'],
                                machine_id=machine, status='submitting', replay_allowed=False)
        _write(directory, state)
        result = submit_once(service, directory, proposal, machine_id=machine,
                             episode_run_id=snapshot['episode_run_id'])
        state['pending']['status'] = result['status']
        if result['status'] == 'native_rejected':
            state['last_post'] = {'status': 'native_rejected', 'operational_retreat_verified': False,
                                  'replay_allowed': False, 'command_causation_verified': False}
            state['pending'] = None
        state['preview'] = None
        _write(directory, state)
    elif kind == 'observe':
        intent = state['pending']
        if intent is None or intent != job['intent'] or intent.get('machine_id') != machine:
            raise ValueError('original retreat intent or machine changed')
        state['last_attempt'] = {'kind': kind, 'frame': _frame(snapshot)}
        _write(directory, state)
        args = intent['arguments']
        try:
            read = service.query_battle_transition_v1(args['expected_combat_id'],
                                                      expected_revision=snapshot['revision'])
            current = service.snapshot(include_native_command_history=False)
            result = verify_independent_post(intent, current, read.get('battle_transition_snapshot'))
            if result.get('reason') == 'original_combat_not_available_requires_existing_terminal_query':
                read = service.query_battle_terminal_transition_v1(args['expected_combat_id'],
                    args['selected_public_cunit_id'], expected_revision=current['revision'])
                current = service.snapshot(include_native_command_history=False)
                result = verify_terminal_post(intent, current, read.get('battle_terminal_transition'))
        except Exception as error:
            result = {'status': 'independent_post_pending', 'operational_retreat_verified': False,
                      'error': f'{type(error).__name__}: {error}', 'replay_allowed': False}
        state['last_post'] = result
        if result.get('operational_retreat_verified') is True:
            state['pending'] = None
        _write(directory, state)
    else:
        raise ValueError('unknown ordinary retreat stage')
    return {'status': 'executed', 'selected_step': planned['plan']['selected_step'],
            'snapshot_id': planned['snapshot_id'], 'revision': planned['revision'],
            'plan': planned['plan'], 'result': result}
