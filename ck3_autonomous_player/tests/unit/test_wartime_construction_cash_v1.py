"""User war spending rule through real policy and ordinary consumer, no CK3."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from test_war_reinforcement_tradeoff_v1 import WarDriver, company, context
from xar_autoplayer.construction_formal_consumer import plan_construction_private
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer.wartime_construction_cash_v1 import observe_wartime_construction_cash_v1
from xar_autoplayer.war_mercenary_consumer_v1 import plan_war_mercenary_turn_v1
from xar_autoplayer.construction_formal_consumer import write_construction_ledger


def inputs(driver):
    snapshot = driver.snapshot
    snapshot['active_wars'][0]['player_relative_war_score'] = 40
    snapshot['played_character_gold']['raw'] = 100000000
    frame = observed_frame(snapshot)
    return dict(root=snapshot['campaign_root_context'],
        spending={'status': 'observed', 'frame': {'actor_character_id': frame['played_character_id'],
            'native_revision': frame['native_revision'], 'date_raw': frame['date_raw'], 'snapshot_id': frame['snapshot_id']},
            'budget': {'active_war_count': 1, 'reserved_raw': {'gold': 0}}},
        market=context(snapshot, [company(7, 10000000, 1400, 9999), company(8, 30000000, 1800, 9998)]),
        market_source_frame=frame, mercenary_ledger={'pending': None, 'observed': []})


@pytest.mark.parametrize('kind', ['new_building', 'upgrade_building'])
def test_winning_war_only_spends_when_military_and_native_emergency_cash_remain(tmp_path, kind):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    values['spending']['budget']['reserved_raw']['gold'] = 7000000
    decision = observe_wartime_construction_cash_v1(driver.snapshot, kind=kind,
        construction_gold_raw=23000000, **values)
    assert decision['new_spend_allowed'] is True
    assert decision['required_remaining_gold_raw'] == 77000000
    assert decision['emergency_company_quote']['company_id'] == 8
    assert len(decision['mercenary_quote_comparisons']) == 2
    too_much = observe_wartime_construction_cash_v1(driver.snapshot, kind=kind,
        construction_gold_raw=23000001, **values)
    assert too_much['new_spend_allowed'] is False
    assert too_much['does_not_open_or_refresh_mercenary_procurement_epoch'] is True
    assert too_much['future_income_credited_raw'] == too_much['loan_or_refund_credited_raw'] == 0


def test_new_holding_has_same_cash_domain_but_no_fabricated_native_action(tmp_path):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    decision = observe_wartime_construction_cash_v1(driver.snapshot, kind='new_holding',
        construction_gold_raw=1, **values)
    assert decision['new_spend_allowed'] is False
    assert decision['reason'] == 'new_holding_native_action_interface_unavailable'


@pytest.mark.parametrize('missing', ['maintenance', 'market', 'old_market', 'can_hire', 'can_afford',
    'complete_cost', 'spending', 'pending_mercenary', 'enemy_at_spawn'])
def test_missing_or_illegal_inputs_defer_only_new_optional_outlay(tmp_path, missing):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    if missing == 'maintenance':
        values['root']['player_max_monthly_gold_maintenance_v1']['status'] = 'unavailable'
    elif missing == 'market':
        values['market'] = None
    elif missing == 'old_market':
        values['market_source_frame'] = {**values['market_source_frame'], 'native_revision': 1}
    elif missing == 'spending':
        values['spending'] = {'status': 'unavailable'}
    elif missing == 'pending_mercenary':
        values['mercenary_ledger']['pending'] = {'status': 'submission_unresolved'}
    else:
        for row in values['market']['rows']:
            if missing in {'can_hire', 'can_afford'}:
                row['final_terms'][missing] = False
            elif missing == 'complete_cost':
                row['final_terms']['resource_costs_raw'] = [10000000]
            else:
                row['location']['hire_auto_raise_province_id'] = driver.snapshot['active_wars'][0]['enemy_armies'][0]['current_province_id']
    assert observe_wartime_construction_cash_v1(driver.snapshot, kind='new_building',
        construction_gold_raw=1, **values)['new_spend_allowed'] is False


def test_current_maximum_military_cost_drives_buffer_without_multiplying_war_count(tmp_path):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    values['root']['player_max_monthly_gold_maintenance_v1']['value']['raw'] = 4000000
    driver.snapshot['active_wars'].append(deepcopy(driver.snapshot['active_wars'][0]))
    driver.snapshot['active_wars'][-1]['war_id'] = 991
    values['spending']['budget']['active_war_count'] = 2
    decision = observe_wartime_construction_cash_v1(driver.snapshot, kind='upgrade_building',
        construction_gold_raw=0, **values)
    assert decision['required_remaining_gold_raw'] == 4000000 * 24 + 30000000
    assert decision['new_spend_allowed'] is False


def test_winning_or_unknown_war_advance_continues_without_optional_queries(tmp_path):
    driver = WarDriver(tmp_path)
    inputs(driver)
    baseline = {'revision': driver.snapshot['revision'], 'plan': {'selected_step': 'life-advance'}}
    with patch('xar_autoplayer.bridge.domain_construction_private_transport_v1.query_construction_private',
            side_effect=AssertionError('optional construction must not query with missing cash inputs')):
        result = plan_construction_private(driver, baseline, driver.snapshot, [], {'life-advance'})
    assert result['plan']['selected_step'] == 'life-advance'
    assert result['plan']['phase'] == 'construction_wartime_cash_deferred'
    assert driver.requests == []
    unknown = {**driver.snapshot, 'active_wars': None}
    result = plan_construction_private(driver, baseline, unknown, [], {'life-advance'})
    assert result['plan']['selected_step'] == 'life-advance'


def test_peaceful_construction_cash_policy_is_unchanged(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot['active_wars'] = []
    assert observe_wartime_construction_cash_v1(driver.snapshot, kind='new_building',
        construction_gold_raw=1)['status'] == 'outside_wartime'


def test_crisis_consumer_explains_cancel_and_debt_gaps_without_sending_or_crediting_funds(tmp_path):
    driver = WarDriver(tmp_path)
    driver.snapshot['active_wars'][0]['player_relative_war_score'] = -80
    driver.snapshot['played_character_gold']['raw'] = 10000000
    write_construction_ledger(tmp_path, {'schema': 'xar.ck3.construction_formal_pending_v1',
        'pending': {'status': 'submission_unresolved', 'episode_run_id': driver.snapshot['episode_run_id']}, 'applied': None})
    plan = plan_war_mercenary_turn_v1(driver, {'selected_step': 'life-advance'}, snapshot=driver.snapshot,
        history=[], bridge_capabilities=set())
    diagnostic = plan['war_financing_capability_gap_v1']
    assert diagnostic['construction_intent_present'] is True
    assert diagnostic['current_active_project_independently_observed'] is False
    assert diagnostic['cancel_construction']['refund_quote_raw'] is None
    assert diagnostic['legal_debt']['principal_quote_raw'] is None
    assert diagnostic['unreceived_funding_credited_raw'] == 0
    assert not diagnostic['cancel_construction']['submit_planned']
    assert not diagnostic['legal_debt']['submit_planned']
    assert plan['selected_step'] == 'life-advance' and driver.requests == [] and driver.hire_count == 0


def test_submit_rechecks_current_inputs_before_creating_intent_or_native_send(tmp_path):
    from test_g2_wartime_construction_service_compound_v1 import WartimeConstructionDriver
    from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.construction_formal_consumer import read_construction_ledger

    driver = WartimeConstructionDriver(tmp_path)
    with patch.object(transport, '_identity', return_value=(881, 'synthetic-wartime-cash-test')):
        query = transport.query_construction_private(driver, expected_revision=driver.snapshot['revision'])
        assert query['status'] == 'selected'
        # An old plan/admission cannot replace the current Native market input.
        driver.recorded = [(step, result) for step, result in driver.recorded
                           if step != 'query-player-mercenary-context-v1']
        with pytest.raises(BridgeUnavailableError, match='wartime optional construction deferred'):
            transport.submit_construction_private(driver, query=query, expected_revision=driver.snapshot['revision'])
    assert read_construction_ledger(tmp_path)['pending'] is None
    assert all(row['step'] != transport.ACTION_NATIVE for row in driver.requests)


def test_weak_cheap_company_cannot_replace_a_quote_covering_known_deficit(tmp_path):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    driver.snapshot['active_wars'][0]['player_relative_war_score'] = -60
    values['market']['rows'][0]['troop_strength']['current_soldiers'] = 50
    decision = observe_wartime_construction_cash_v1(driver.snapshot, kind='new_building',
        construction_gold_raw=0, **values)
    assert decision['observed_focused_headcount_deficit'] == 700
    assert decision['emergency_company_quote']['company_id'] == 8
    assert decision['emergency_quote_reserve_policy'] == 'cheapest_current_legal_quote_covering_focused_observed_headcount_deficit'
    values['market']['rows'] = []
    empty = observe_wartime_construction_cash_v1(driver.snapshot, kind='new_building', construction_gold_raw=0, **values)
    assert empty['market_observation'] == 'complete_empty'
    assert empty['reason'] == 'complete_market_empty_no_emergency_company'
    unknown = observe_wartime_construction_cash_v1(driver.snapshot, kind='new_building', construction_gold_raw=0,
        **{**values, 'market': None})
    assert unknown['reason'] == 'same_frame_available_mercenary_emergency_quotes_unobserved'


def test_current_assessed_suitable_quote_has_priority_but_old_decision_does_not(tmp_path):
    driver = WarDriver(tmp_path)
    values = inputs(driver)
    driver.snapshot['active_wars'][0]['player_relative_war_score'] = -60
    frame = values['market_source_frame']
    selected = {'company_id': 8, 'gold_cost_raw': 30000000, 'rejection_reasons': [],
        'purpose_war_ids': [driver.snapshot['active_wars'][0]['war_id']],
        'finance': {'source_frame': {'actor_character_id': frame['played_character_id'],
            'native_revision': frame['native_revision'], 'date_raw': frame['date_raw']}}}
    decision = observe_wartime_construction_cash_v1(driver.snapshot, kind='upgrade_building',
        construction_gold_raw=0, procurement_decision={'selected_candidate': selected}, **values)
    assert decision['emergency_company_quote']['company_id'] == 8
    assert decision['emergency_quote_reserve_policy'] == 'current_frame_assessed_suitable_procurement_quote'
    selected['finance']['source_frame']['native_revision'] -= 1
    later = observe_wartime_construction_cash_v1(driver.snapshot, kind='upgrade_building',
        construction_gold_raw=0, procurement_decision={'selected_candidate': selected}, **values)
    assert later['emergency_company_quote']['company_id'] == 7
