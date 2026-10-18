"""Financing source availability never becomes a loan action or received cash."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.ingame_decision_outcome_contract import CAPABILITY
from xar_autoplayer.construction_formal_consumer import write_construction_ledger
from xar_autoplayer.war_mercenary_consumer_v1 import plan_war_mercenary_turn_v1
from xar_autoplayer.wartime_construction_cash_v1 import observe_war_financing_capability_gap_v1


def inputs():
    snapshot = {'played_character': {'character_id': 41}, 'native_revision': 12,
        'revision': 7, 'date_raw': 53300000, 'snapshot_id': 'synthetic-financing-frame',
        'episode_run_id': 'synthetic-financing-episode', 'paused': True, 'map_ready': True,
        'active_event': None, 'pending_character_interaction': None,
        'played_character_gold': {'raw': 25000000, 'scale': 100000},
        'player_armies': [],
        'active_wars': [{'war_id': 99, 'player_is_primary_war_leader': True,
            'player_side': 'defender', 'player_relative_war_score': -80,
            'targeted_title_ids': [2230], 'enemy_armies': []}]}
    priority = {'wars': [{'war_id': 99, 'primary_player_war': True,
        'player_relative_war_score': -80, 'raised_force_deficit': True}]}
    root = {'status': 'available', 'player_character_id': 41,
        'snapshot_revision': 12, 'date_raw': 53300000,
        'player_max_monthly_gold_maintenance_v1': {
            'status': 'available', 'value': {'raw': 2000000, 'scale': 100000}}}
    return snapshot, {'priority': priority, 'root': root, 'construction_ledger': {'pending': None}}


@pytest.mark.parametrize('advertised', [False, True])
def test_existing_confirm_source_and_advertisement_do_not_qualify_borrowing(advertised):
    snapshot, values = inputs()
    result = observe_war_financing_capability_gap_v1(snapshot, **values,
        bridge_capabilities={CAPABILITY} if advertised else set())
    debt = result['legal_debt']
    route = debt['source_reviewed_confirm_route']
    assert route['public_tool'] == 'ck3_confirm_ingame_decision_outcome_v1'
    assert route['capability'] == CAPABILITY
    assert route['advertised_in_supplied_bridge_capabilities'] is advertised
    assert route['decision_key'] == 'borrow_from_holy_order_decision'
    assert route['expected_event_definition_key'] == 'holy_order.0200'
    assert route['current_selected_legal_decision_verified'] is False
    assert route['dispatch_or_expected_event_proves_received_funds'] is False
    assert debt['source_reviewed_debt_commit_option'] == 'holy_order.0200.a'
    assert debt['current_build_full_terms_verified'] is False
    assert debt['typed_debt_readback_verified'] is False
    assert debt['independently_attributed_received_funds_verified'] is False
    assert debt['principal_quote_raw'] is None and debt['submit_planned'] is False
    assert result['cancel_construction']['refund_quote_raw'] is None
    assert result['cancel_construction']['submit_planned'] is False
    assert result['unreceived_funding_credited_raw'] == 0
    assert result['future_funding_receipts_must_keep_same_procurement_epoch'] is True
    assert result['unknown_submission_must_not_be_replayed'] is True


@pytest.mark.parametrize('field,value', [('player_character_id', 42), ('snapshot_revision', 11),
    ('date_raw', 53300024), ('status', 'unavailable')])
def test_old_or_wrong_root_cannot_be_reported_as_current_maintenance(field, value):
    snapshot, values = inputs()
    values['root'][field] = value
    result = observe_war_financing_capability_gap_v1(snapshot, **values)
    assert result['ordinary_military_buffer_raw'] is None
    assert result['maximum_military_maintenance_status'] == 'unobserved'
    assert result['legal_debt']['source_reviewed_confirm_route'][
        'advertised_in_supplied_bridge_capabilities'] is None


def test_only_current_known_maintenance_triggers_its_larger_shortfall():
    snapshot, values = inputs()
    values['priority']['wars'][0]['player_relative_war_score'] = 40
    result = observe_war_financing_capability_gap_v1(snapshot, **values)
    assert result['ordinary_military_buffer_raw'] == 36000000
    assert result['maximum_military_maintenance_status'] == 'same_frame_observed'
    values['root']['snapshot_revision'] -= 1
    assert observe_war_financing_capability_gap_v1(snapshot, **values) is None


@pytest.mark.parametrize('active', [[], None, [{'war_id': 100}]])
def test_historical_priority_is_not_a_current_financing_crisis(active):
    snapshot, values = inputs()
    snapshot['active_wars'] = active
    assert observe_war_financing_capability_gap_v1(snapshot, **values) is None


def test_unobserved_cash_is_not_zero_or_boolean_money():
    snapshot, values = inputs()
    snapshot['played_character_gold']['raw'] = False
    result = observe_war_financing_capability_gap_v1(snapshot, **values)
    assert result['observed_treasury_raw'] is None
    assert result['unreceived_funding_credited_raw'] == 0


def test_ordinary_consumer_keeps_pending_receipt_and_war_action_even_with_confirm_capability(tmp_path):
    snapshot, _ = inputs()
    snapshot['played_character_gold']['raw'] = 10000000

    class Driver:
        state_dir = tmp_path

        def execute_step(self, *args, **kwargs):
            pytest.fail('financing diagnostic must not query or send an action')

    write_construction_ledger(tmp_path, {'schema': 'xar.ck3.construction_formal_pending_v1',
        'pending': {'status': 'submission_unresolved', 'episode_run_id': snapshot['episode_run_id']},
        'applied': None})
    baseline = {'selected_step': 'life-advance'}
    before = deepcopy(snapshot)
    plan = plan_war_mercenary_turn_v1(Driver(), baseline, snapshot=snapshot,
        history=[], bridge_capabilities={CAPABILITY})
    assert snapshot == before and baseline == {'selected_step': 'life-advance'}
    assert plan['selected_step'] == 'life-advance'
    assert plan['war_mercenary_status'] == 'existing_construction_pending_receipt_keeps_priority'
    assert plan['war_financing_capability_gap_v1']['legal_debt']['submit_planned'] is False
    assert plan['war_financing_capability_gap_v1']['unreceived_funding_credited_raw'] == 0
    text = plan['war_decision_presentation_v1']['reason']
    assert '取消工程与合法借款仍待当帧条款及独立到账核验' in text
    assert '借款执行通道' not in text
