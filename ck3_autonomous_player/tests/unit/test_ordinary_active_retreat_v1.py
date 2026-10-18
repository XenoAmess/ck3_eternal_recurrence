"""Ordinary retreat production stages, synthetic endpoints only; no live credit."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

import test_battle_current_retreat_policy as fixture
import test_active_combat_retreat_v1_bridge as native_fixture
import test_battle_terminal_transition_v1_bridge as terminal_fixture
from test_war_reinforcement_tradeoff_v1 import WarDriver
from xar_autoplayer import strategy
from xar_autoplayer import war_active_retreat_v1 as policy
from xar_autoplayer.bridge import ordinary_retreat_service_v1 as consumer
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError

MACHINE = 'synthetic-machine-identity'
CAPS = set(policy._ACTIVE_COMBAT_RETREAT_V1_REQUIRED_CAPABILITIES) | {
    'game.command.query-battle-transition-v1-N', 'game.command.query-battle-terminal-transition-v1'}


def scene():
    control = fixture._normalized_frame(1)
    actor, subject = control['selected_owner_character_id'], control['selected_public_cunit_id']
    origin = control['combat_province_id']
    snapshot = {'snapshot_id': 'fixture-current-retreat', 'revision': 7,
        'native_revision': control['snapshot_revision'], 'date_raw': control['observed_date_raw'],
        'episode_run_id': 'fixture-current-retreat', 'paused': True, 'map_ready': True,
        'active_event': None, 'pending_character_interaction': None, 'one_life_settlement': None,
        'diagnostics': {'connection_generation': 1}, 'played_character': {'character_id': actor, 'alive': True},
        'player_armies': [{'army_id': subject, 'owner_character_id': actor, 'soldiers': 10,
            'controllable': True, 'in_combat': True, 'retreating': False, 'army_state': 'combat',
            'current_province_id': origin, 'move_target_province_id': None, 'route_province_ids': []},
            {'army_id': 900, 'owner_character_id': actor, 'soldiers': 500,
             'controllable': True, 'in_combat': False, 'retreating': False, 'army_state': 'regular',
             'current_province_id': 2579, 'move_target_province_id': None, 'route_province_ids': []}],
        'active_wars': [{'war_id': 88, 'player_is_primary_war_leader': True,
            'player_side': 'defender', 'player_relative_war_score': -30, 'targeted_title_ids': [2231],
            'enemy_armies': [{'army_id': 357, 'current_province_id': origin,
                'move_target_province_id': None, 'route_province_ids': [], 'route_read_status': 'complete_empty'}]}]}
    snapshot.update(battle_control_snapshot_v1=control, battle_control_snapshot_v1_status='available',
        battle_control_snapshot_v1_subject_army_id=subject, battle_control_snapshot_v1_query_sequence=1,
        battle_control_snapshot_v1_queried_snapshot_id=snapshot['snapshot_id'],
        battle_control_snapshot_v1_queried_revision=snapshot['revision'])
    return snapshot, control, fixture._preview(control)


BASE = {'policy': 'one-life-turn-v1', 'phase': 'native_war_global_battle_control_progress',
        'selected_step': 'life-advance', 'reason': 'normal observed battle'}


def planned(tmp_path, snapshot=None, base=None):
    snapshot = snapshot or scene()[0]
    driver = SimpleNamespace(state_dir=tmp_path)
    answer = consumer.plan_ordinary_retreat_v1(driver, dict(base or BASE), snapshot=snapshot,
                                               history=[], bridge_capabilities=CAPS)
    return {'snapshot_id': snapshot['snapshot_id'], 'revision': snapshot['revision'], 'plan': answer}


def envelope(snapshot, plan):
    return {'snapshot_id': snapshot['snapshot_id'], 'revision': snapshot['revision'], 'plan': plan}


@pytest.fixture
def machine_reader():
    with patch('xar_autoplayer.bridge.relic_action_private_transport._machine_identity',
               return_value=(MACHINE, 'a' * 64, {'policy_version': 'synthetic', 'protection_max_hours': 168})):
        yield


class TypedService:
    def __init__(self, directory):
        self.driver = SimpleNamespace(state_dir=directory)
        self.current, self.control, self.preview = scene()
        self.preview_calls = self.order_calls = self.transition_calls = self.terminal_calls = 0
        self.order_error = None
        self.ack = {'accepted': True, 'status': 'accepted_verification_pending'}
        self.transition = None
        self.terminal = None

    def _strategy_state_dir(self):
        return self.driver.state_dir

    def snapshot(self, **kwargs):
        return copy.deepcopy(self.current)

    def preview_active_combat_retreat_v1(self, *args, **kwargs):
        self.preview_calls += 1
        return copy.deepcopy(self.preview)

    def order_active_combat_retreat_v1(self, **kwargs):
        self.order_calls += 1
        if self.order_error:
            raise self.order_error
        return copy.deepcopy(self.ack)

    def query_battle_transition_v1(self, *args, **kwargs):
        self.transition_calls += 1
        return {'battle_transition_snapshot': self.transition}

    def query_battle_terminal_transition_v1(self, *args, **kwargs):
        self.terminal_calls += 1
        return {'battle_terminal_transition': self.terminal}


def execute(service, selected):
    return GameplayBridgeService._execute_planned_turn_without_unhandled_capture(service, selected)


def order(service, tmp_path):
    first = planned(tmp_path, service.current)
    assert first['plan']['selected_step'] == consumer.PREVIEW
    execute(service, first)
    second = planned(tmp_path, service.current)
    assert second['plan']['selected_step'] == consumer.ORDER
    return execute(service, second)


def post_scene(service):
    service.current.update(snapshot_id='independent-post', revision=8, native_revision=6)
    subject = service.current['player_armies'][0]
    subject.update(in_combat=False, retreating=True, army_state='retreating',
                   move_target_province_id=2579, route_province_ids=[2579])
    service.transition = {'schema_version': 1, 'contract_stage': 'production_exact_combat_lifecycle',
        'status': 'available', 'battle_transition_ready': True, 'snapshot_revision': 6,
        'observed_date_raw': service.current['date_raw'], 'combat_id': service.control['combat_id'],
        'province_id': service.control['province_id'], 'phase': 'pursuit', 'phase_raw': 2, 'phase_day': 0,
        'winner_side': 'defender', 'winner_raw': 1, 'forced_winner_side': 'none', 'forced_winner_raw': -1,
        'finalized': False, 'battle_result_id': None,
        'attacker_public_cunit_ids_in_stored_order': service.control['affected_public_cunit_ids_in_stored_order'],
        'defender_public_cunit_ids_in_stored_order': [999]}


def test_explicit_budget_is_current_owner_not_global_semantic_headcount():
    snapshot, control, _ = scene()
    budget = policy.normal_retreat_loss_budget(snapshot, control)
    assert budget['maximum_next_tick_hard_loss_raw'] == 50_000
    assert budget['owner_current_fighting_raw'] == 1_000_000
    snapshot['player_armies'][0]['soldiers'] = 999_999
    assert policy.normal_retreat_loss_budget(snapshot, control) == budget
    assert budget['battle_win_probability'] is None
    assert budget['defeat_title_transfer_verified'] is False


@pytest.mark.parametrize('change', ['score', 'attacker', 'no_targets', 'not_primary', 'unrelated_war', 'stronger'])
def test_unsupported_stakes_or_no_current_disadvantage_preserve_ordinary_plan(tmp_path, change):
    snapshot, control, _ = scene()
    war = snapshot['active_wars'][0]
    if change == 'score': war['player_relative_war_score'] = 0
    elif change == 'attacker': war['player_side'] = 'attacker'
    elif change == 'no_targets': war['targeted_title_ids'] = []
    elif change == 'not_primary': war['player_is_primary_war_leader'] = False
    elif change == 'unrelated_war': war['enemy_armies'][0]['army_id'] = 999
    else: control['attacker']['derived_current_fighting_raw'] += 1
    assert policy.normal_retreat_loss_budget(snapshot, control)['status'] == 'unavailable'
    assert planned(tmp_path, snapshot)['plan']['selected_step'] == 'life-advance'


@pytest.mark.parametrize('change', ['modal', 'concrete_order', 'sole_army', 'enemy_route_unknown', 'enemy_rally'])
def test_mandatory_and_incomplete_or_hostile_rally_never_propose_retreat(tmp_path, change):
    snapshot, _, _ = scene()
    base = dict(BASE)
    if change == 'modal': snapshot['active_event'] = {'instance_id': 77}
    elif change == 'concrete_order': base['selected_step'] = 'move-army-900-to-2578'
    elif change == 'sole_army': snapshot['player_armies'].pop()
    elif change == 'enemy_route_unknown': snapshot['active_wars'][0]['enemy_armies'][0].pop('route_read_status')
    else:
        snapshot['active_wars'][0]['enemy_armies'][0].update(
            route_read_status='complete_nonempty', move_target_province_id=2579, route_province_ids=[2579])
    assert planned(tmp_path, snapshot, base)['plan']['selected_step'] == base['selected_step']


def test_real_battle_state_reader_and_native_partial_operands_gate_planner(tmp_path):
    snapshot, control, _ = scene()
    state = strategy._battle_control_turn_state([], snapshot, snapshot['player_armies'])
    assert state['status'] == 'ready'
    result = planned(tmp_path, snapshot)
    assert result['plan']['selected_step'] == consumer.PREVIEW
    control.pop('current_loss_inputs_v1')
    assert planned(tmp_path, snapshot)['plan']['selected_step'] == 'life-advance'


def test_normal_service_executor_displays_before_preview_and_can_intercept(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    selected = planned(tmp_path)
    intercepted = GameplayBridgeService._execute_planned_turn_without_unhandled_capture(
        service, selected, before_submit=lambda frame: {'status': 'test_intercept'})
    assert intercepted['status'] == 'intercepted' and service.preview_calls == 0
    frames = []
    result = GameplayBridgeService._execute_planned_turn_without_unhandled_capture(
        service, selected, before_submit=lambda frame: frames.append(frame))
    assert frames[0]['selected_step'] == consumer.PREVIEW
    assert result['status'] == 'executed' and service.preview_calls == 1 and service.order_calls == 0


def test_exact_preview_order_ack_then_independent_original_combat_post(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    result = order(service, tmp_path)
    assert result['result']['operational_retreat_verified'] is False
    assert service.order_calls == 1
    post_scene(service)
    result = execute(service, planned(tmp_path, service.current))
    assert result['result']['operational_retreat_verified'] is True
    assert result['result']['war_outcome_verified'] is False
    assert consumer._read(tmp_path)['pending'] is None
    # A preserved exclusion still forbids a second send for the original ID.
    service.current, _, _ = scene()
    assert planned(tmp_path, service.current)['plan']['selected_step'] == 'life-advance'
    assert service.order_calls == 1


def test_unknown_submission_survives_new_service_and_does_not_resend(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    service.order_error = TimeoutError('synthetic lost ACK')
    result = order(service, tmp_path)
    assert result['result']['status'] == 'unknown' and service.order_calls == 1
    cold = TypedService(tmp_path)
    result = execute(cold, planned(tmp_path, cold.current))
    assert result['result']['operational_retreat_verified'] is False
    assert cold.order_calls == 0
    assert planned(tmp_path, cold.current)['plan']['selected_step'] == 'life-advance'


def test_known_native_rejection_keeps_exclusion_without_effect_credit(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    service.ack = {'accepted': False, 'status': 'rejected', 'rejection_reason': 'route_changed'}
    result = order(service, tmp_path)
    assert result['result']['status'] == 'native_rejected'
    assert consumer._read(tmp_path)['pending'] is None
    assert consumer._read(tmp_path)['last_post']['operational_retreat_verified'] is False
    assert planned(tmp_path)['plan']['selected_step'] == 'life-advance'
    assert service.order_calls == 1


def test_stale_preview_or_frame_never_reuses_token(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    execute(service, planned(tmp_path))
    stale = planned(tmp_path)
    service.current['revision'] += 1
    with pytest.raises(ValueError, match='source frame changed'):
        execute(service, stale)
    assert service.order_calls == 0


@pytest.mark.parametrize('change', ['owner', 'combat', 'target', 'connection', 'same_frame'])
def test_independent_active_post_identity_changes_keep_original_pending(tmp_path, machine_reader, change):
    service = TypedService(tmp_path)
    order(service, tmp_path)
    intent = consumer._read(tmp_path)['pending']
    post_scene(service)
    if change == 'owner': service.current['player_armies'][0]['owner_character_id'] += 1
    elif change == 'combat': service.transition['combat_id'] += 1
    elif change == 'target': service.current['player_armies'][0]['move_target_province_id'] += 1
    elif change == 'connection': service.current['diagnostics']['connection_generation'] += 1
    else: service.current.update(revision=7, snapshot_id='fixture-current-retreat')
    result = policy.verify_independent_post(intent, service.current, service.transition)
    assert result['operational_retreat_verified'] is False and result['replay_allowed'] is False


def test_oversized_corrupt_state_keeps_original_battle_action(tmp_path):
    (tmp_path / consumer.LEDGER).write_text('{"schema":"ordinary-active-retreat/v1"}')
    result = planned(tmp_path)
    assert result['plan']['selected_step'] == 'life-advance'
    assert result['plan'][consumer.FIELD]['status'] == 'unavailable'


def test_real_native_service_repreview_changed_route_prevents_move(tmp_path, machine_reader):
    # The exact existing NativeDriver orders are exercised, not a permissive
    # policy stub. The old fixture merely supplies DTO construction helpers.
    driver, endpoint = native_fixture._driver(routes=[[native_fixture.TARGET_PROVINCE], [9999, native_fixture.TARGET_PROVINCE]])
    service = GameplayBridgeService(driver)
    before = service.snapshot()
    preview = service.preview_active_combat_retreat_v1(native_fixture.SELECTED,
        native_fixture.TARGET_PROVINCE, expected_revision=before['revision'])
    rejected = service.order_active_combat_retreat_v1(native_fixture.SELECTED,
        expected_revision=preview['source_binding']['revision'], expected_combat_id=native_fixture.COMBAT_ID,
        expected_side_index=0, expected_scope='full_side', target_province_id=native_fixture.TARGET_PROVINCE,
        candidate_token=preview['target_preview']['candidate_token'])
    assert rejected['accepted'] is False and rejected['rejection_reason'] == 'route_changed'
    assert endpoint.move_count == 0 and endpoint.route_preview_count == 2


def terminal_scene(service):
    terminal = terminal_fixture._normal_frame()
    terminal.update(snapshot_revision=service.current['native_revision'],
        observed_date_raw=service.current['date_raw'], prior_combat_id=service.control['combat_id'],
        subject_public_cunit_id=service.control['selected_public_cunit_id'])
    terminal['terminal_journal']['requested_after_sequence'] = None
    prior = terminal['prior']
    prior.update(combat_id=service.control['combat_id'], winner_raw=1,
        terminal_date_raw=service.current['date_raw'],
        attacker_public_cunit_ids_in_stored_order=service.control['affected_public_cunit_ids_in_stored_order'])
    prior['battle_warscore'].update(winner_is_war_attacker=False)
    terminal['subject'].update(combat_backlink_id=None, active_combat_id=None,
        movement_or_retreat_state_raw=1, blocked_by_active_combat=False, ai_membership_status='none',
        coordinator_id=None, unit_stack_stored_index=None, subunit_stored_index=None)
    terminal['successor'].update(state='subject_retreating', matching_combat_ids_in_native_order=[],
        selected_successor_combat_id=None, participant_overlap_public_cunit_ids_in_prior_order=[])
    return terminal


def test_removed_original_combat_uses_real_terminal_normalizer_and_core(tmp_path, machine_reader):
    service = TypedService(tmp_path)
    order(service, tmp_path)
    post_scene(service)
    service.transition.update(status='combat_not_found', battle_transition_ready=True)
    # The existing strict transition's removed form is supplied below by the
    # fixture normalizer helper; no fabricated available lifecycle is accepted.
    from xar_autoplayer.bridge.battle_transition_contract import normalize_battle_transition_v1
    raw = dict(service.transition)
    for key in ('province_id', 'phase', 'phase_raw', 'phase_day', 'winner_side', 'winner_raw',
                'forced_winner_side', 'forced_winner_raw', 'finalized', 'battle_result_id'):
        raw[key] = None
    raw['attacker_public_cunit_ids_in_stored_order'] = []
    raw['defender_public_cunit_ids_in_stored_order'] = []
    service.transition = normalize_battle_transition_v1(raw,
        expected_combat_id=service.control['combat_id'], expected_observed_date_raw=service.current['date_raw'],
        expected_snapshot_revision=service.current['native_revision'])
    service.terminal = terminal_scene(service)
    result = execute(service, planned(tmp_path, service.current))
    assert service.terminal_calls == 1
    assert result['result']['operational_retreat_verified'] is True
    assert result['result']['war_outcome_verified'] is False


@pytest.mark.parametrize('change', ['wrong_combat', 'suppressed', 'reentry', 'wrong_target', 'wrong_actor'])
def test_terminal_absence_or_changed_scope_never_credits_retreat(tmp_path, machine_reader, change):
    service = TypedService(tmp_path)
    order(service, tmp_path)
    intent = consumer._read(tmp_path)['pending']
    post_scene(service)
    terminal = terminal_scene(service)
    if change == 'wrong_combat': terminal['prior_combat_id'] += 1
    elif change == 'suppressed': terminal['prior']['terminal_kind'] = 'no_normal_result'
    elif change == 'reentry': terminal['successor']['state'] = 'residual_new_combat'
    elif change == 'wrong_target': terminal['subject']['move_target_province_id'] += 1
    else: service.current['played_character']['character_id'] += 1
    result = policy.verify_terminal_post(intent, service.current, terminal)
    assert result['operational_retreat_verified'] is False
    assert result['replay_allowed'] is False


def test_real_service_normal_plan_stages_retreat_before_procurement(tmp_path, machine_reader):
    driver = WarDriver(tmp_path)
    snapshot, _, _ = scene()
    driver.snapshot.update(snapshot)
    driver.snapshot.update(army_routes_supported=False, move_route_preview_supported=False,
                           route_contact_horizon_supported=False)
    driver.capabilities = lambda: {'action_steps': ['life-advance'], 'bridge_capabilities': list(CAPS)}
    service = GameplayBridgeService(driver)
    planned_turn = service.plan_turn()
    assert planned_turn['plan']['selected_step'] == consumer.PREVIEW
    assert planned_turn['plan']['phase'] == 'native_war_active_retreat_preview'
    assert driver.query_count == driver.hire_count == driver.advance_count == 0


def test_real_service_auto_turn_through_native_endpoint_preview_order(tmp_path, machine_reader):
    from xar_autoplayer.bridge.version_identity import CK3_12004
    class Endpoint:
        pipe_name = r'\\.\pipe\synthetic-ordinary-retreat-production-path'
        def __init__(self):
            self.sent = []
            self.moves = 0
            self.snapshot, self.control, _ = scene()
            self.snapshot['phase'] = 'map_hud'
            self.snapshot['date'] = '1066.9.27'
            self.snapshot['speed'] = 1
            self.snapshot['history'] = []
            self.snapshot['active_wars'][0].update(primary_opponent_character_id=36108,
                allied_armies=copy.deepcopy(self.snapshot['player_armies']),
                war_objective_province_ids=[], objective_province_states=[])
            self.snapshot['active_wars'][0]['enemy_armies'][0].update(
                army_id=357, owner_character_id=36108, soldiers=10, controllable=False,
                in_combat=True, retreating=False, army_state='combat', army_state_code=2,
                route_source_count=0, move_target_observable=False)
        def start(self, on_frame, on_disconnect): self.callback = on_frame
        def publish(self, frame): self.callback(frame)
        def semantic(self, revision=5):
            self.publish({'type': 'state_snapshot', 'protocol_version': 1,
                'snapshot_id': 'native:' + str(revision), 'revision': revision,
                'state': {key: self.snapshot[key] for key in ('phase', 'date', 'date_raw', 'speed',
                    'paused', 'map_ready', 'history', 'active_event', 'pending_character_interaction',
                    'played_character', 'one_life_settlement', 'active_wars', 'player_armies')}})
        def send(self, frame):
            if frame.get('type') != 'execute_step': return
            step = frame['step']
            self.sent.append(step)
            if step.startswith('query-battle-control-snapshot-v1-'):
                result = {'step': step, 'accepted': True, 'status': 'available',
                    'query_sequence': len(self.sent), 'snapshot_revision': 5,
                    'battle_control_snapshot': self.control}
            elif step.startswith('preview-move-army-'):
                result = {'step': step, 'accepted': True, 'status': 'available', 'route_preview': {
                    'status': 'available', 'army_id': self.control['selected_public_cunit_id'],
                    'origin_province_id': self.control['combat_province_id'],
                    'target_province_id': 2579, 'route_province_ids': [2579]}}
            elif step.startswith('move-army-'):
                self.moves += 1
                result = {'step': step, 'accepted': True, 'status': 'submitted'}
            else:
                raise AssertionError('unexpected Native command ' + step)
            self.publish({'type': 'command_result', 'protocol_version': 1,
                'request_id': frame['request_id'], 'ok': True, 'result': result})
        def close(self): pass
        def transport_error(self): return None
    endpoint = Endpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=.05)
    endpoint.publish({'type': 'hello', 'protocol_version': 1, 'bridge_version': '0.1.0', 'pid': 7001,
        'session_generation': 0, 'game_version': CK3_12004.game_version,
        'executable_sha256': CK3_12004.executable_sha256,
        'capabilities': list(CAPS | {'game.state.snapshot', 'game.state.wait-for-change',
            'game.command.set-speed-1', 'game.command.set-speed-3', 'game.command.set-speed-5',
            'game.command.resume-map', 'game.command.pause-map'})})
    endpoint.semantic()
    assert driver.state._last_rejected_state_snapshot is None, driver.state._last_rejected_state_snapshot
    driver.state_dir = tmp_path
    service = GameplayBridgeService(driver)
    service._auto_camera_worker.schedule = lambda _: {'status': 'synthetic_presentation_skipped'}
    service.query_battle_control_snapshot_v1(endpoint.control['selected_public_cunit_id'],
                                            expected_revision=service.snapshot()['revision'])
    displayed = []
    preview = service.auto_turn(before_submit=lambda frame: displayed.append(frame['selected_step']))
    assert preview['selected_step'] == consumer.PREVIEW
    ordered = service.auto_turn(before_submit=lambda frame: displayed.append(frame['selected_step']))
    assert ordered['selected_step'] == consumer.ORDER
    assert endpoint.moves == 1
    assert ordered['result']['operational_retreat_verified'] is False
    assert displayed == [consumer.PREVIEW, consumer.ORDER]
    assert sum(step.startswith('preview-move-army-') for step in endpoint.sent) == 2


def test_h3937_still_inhibits_existing_typed_order_before_native_send():
    driver, endpoint = native_fixture._driver()
    service = GameplayBridgeService(driver)
    before = service.snapshot()
    preview = service.preview_active_combat_retreat_v1(native_fixture.SELECTED,
        native_fixture.TARGET_PROVINCE, expected_revision=before['revision'])
    original_steps = list(endpoint.sent_steps)
    with patch.object(driver, '_h3937_date_hold_active', return_value=True):
        with pytest.raises(BridgeUnavailableError, match='H3937 move hold'):
            service.order_active_combat_retreat_v1(native_fixture.SELECTED,
                expected_revision=preview['source_binding']['revision'], expected_combat_id=native_fixture.COMBAT_ID,
                expected_side_index=0, expected_scope='full_side', target_province_id=native_fixture.TARGET_PROVINCE,
                candidate_token=preview['target_preview']['candidate_token'])
    assert endpoint.sent_steps == original_steps and endpoint.move_count == 0
