"""Future-only crisis cash policy; real ordinary consumers, synthetic game."""
import asyncio
from copy import deepcopy
from unittest.mock import patch

import pytest
from mcp import Client

from test_war_reinforcement_tradeoff_v1 import WarDriver, company, context
from test_war_emergency_budget_v1 import crisis, spending_for, employed, next_frame
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer import war_mercenary_consumer_v1 as consumer
from xar_autoplayer.war_strategic_reserve_v1 import assess_mercenary_reinforcement_v1
from xar_autoplayer.war_emergency_budget_v1 import observe_emergency_recovery_v1


def assess(driver, *, price=34000000, troops=1400, ledger=None, spending=None, rows=None):
    return assess_mercenary_reinforcement_v1(driver.snapshot,
        context(driver.snapshot, rows or [company(7, price, troops, 9999)]),
        campaign_root=driver.snapshot['campaign_root_context'], procurement_ledger=ledger,
        spending_observation=spending_for(driver) if spending is None else spending)


def test_upfront_affordable_does_not_falsify_finance_or_debt_occurrence(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver, level=2)
    decision = assess(driver, price=35000000)
    selected = decision['selected_candidate']
    assert selected['company_id'] == 7 and selected['gold_after_hire_raw'] == 0
    assert selected['finance']['retains_military_allocation'] is False
    assert selected['finance']['maintenance_allocation_months'] == 3
    assert selected['finance']['required_gold_reserve_raw'] == 451200 * 3
    assert selected['finance']['future_gross_income_credited_raw'] == 0
    assert selected['finance']['complete_monthly_net_observed'] is False
    mode = selected['crisis_spend_down_v1']
    assert mode['future_funding_credited_raw'] == 0
    assert mode['future_debt_occurrence_verified'] is False
    assert mode['loan_principal_or_debt_capacity'] is None
    assert mode['overridden_policy_checks'] == ['military_cash_allocation', 'treasury_share_limit']
    assert selected['emergency_budget_revision_v1']['level'] == 3
    assert selected['emergency_marginal_value_v1']['after_company_arrival'] == 2200
    assert selected['arrival_eta_days'] is None and selected['battle_win_probability'] is None
    assert selected['guaranteed_emergency_rescue'] is False


def test_same_epoch_locks_total_cash_and_preserves_other_commitments(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver, level=2)
    first = assess(driver)
    receipt = employed(driver, first)
    ledger = {'pending': None, 'observed': [receipt]}
    next_frame(driver)
    driver.snapshot['played_character_gold']['raw'] = 20000000
    again = assess(driver, price=2000000, ledger=ledger)
    row = again['candidates'][0]
    assert again['selected_company_id'] is None
    assert row['emergency_budget_revision_v1']['epoch_id'] == first['selected_candidate']['emergency_budget_revision_v1']['epoch_id']
    assert row['emergency_budget_revision_v1']['total_package_limit_raw'] == 35000000
    assert row['procurement_package_budget_v1']['remaining_package_gold_raw'] == 1000000
    spending = spending_for(driver)
    spending['budget']['reserved_raw']['gold'] = 19000000
    assert assess(driver, price=2000000, spending=spending)['selected_company_id'] is None
    assert assess(driver, ledger={'pending': receipt, 'observed': []})['selected_company_id'] is None
    forged = deepcopy(receipt)
    forged['decision']['selected_candidate']['emergency_budget_revision_v1']['crisis_spend_down_v1']['future_funding_credited_raw'] = 1
    assert assess(driver, price=500000, ledger={'pending': None, 'observed': [forged]})['selected_company_id'] is None


def test_level3_needs_new_native_frame_and_recovery_uses_ordinary_target(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver, level=2)
    first = assess(driver, price=28000000)
    assert first['selected_candidate']['emergency_budget_revision_v1']['level'] == 2
    receipt = employed(driver, first)
    ledger = {'pending': None, 'observed': [receipt]}
    driver.snapshot['played_character_gold']['raw'] = 7000000
    assert assess(driver, price=7000000, ledger=ledger)['selected_company_id'] is None
    next_frame(driver)
    second = assess(driver, price=7000000, ledger=ledger)
    selected = second['selected_candidate']
    assert selected['emergency_budget_revision_v1']['level'] == 3
    assert selected['emergency_budget_revision_v1']['total_package_limit_raw'] == 35000000
    assert selected['procurement_package_budget_v1']['remaining_package_gold_raw'] == 7000000
    ledger['observed'].append(employed(driver, second, 'synthetic-crisis-b'))
    driver.snapshot['active_wars'] = []
    recovery = observe_emergency_recovery_v1(driver.snapshot, ledger, driver.snapshot['campaign_root_context'])
    assert recovery['defer_new_economic_construction'] is True
    assert recovery['normal_reserve_target_raw'] == 20000000
    assert recovery['future_income_credited_raw'] == 0


def test_full_market_keeps_every_quote_and_prefers_cheaper_adequate_noncrisis(tmp_path):
    driver = WarDriver(tmp_path)
    crisis(driver, level=2)
    rows = [company(7, 34000000, 1400, 9999), company(8, 10000000, 400, 9999),
            company(9, 30000000, 1300, 9999), company(10, 35000000, 4000, 9999)]
    rows[-1]['final_terms']['can_afford'] = False
    decision = assess(driver, rows=rows)
    assert [row['company_id'] for row in decision['candidates']] == [7, 8, 9, 10]
    assert decision['selected_company_id'] == 9
    assert 'crisis_spend_down_v1' not in decision['selected_candidate']
    assert 'native_hire_or_affordability_rejected' in decision['candidates'][-1]['rejection_reasons']


@pytest.mark.parametrize('case', ['success', 'minus100_active', 'ordinary', 'no_major_stakes',
    'no_corroboration', 'attacker', 'war_ended', 'weak_reinforcement', 'native_cannot_hire',
    'native_cannot_afford', 'cash_below_quote', 'incomplete_quote', 'unknown_strength',
    'hostile_at_spawn', 'unknown_pending'])
def test_registered_ordinary_consumer_crisis_and_negatives_keep_advancing(tmp_path, case):
    driver = WarDriver(tmp_path)
    crisis(driver, level=2)
    snapshot = driver.snapshot
    rows = [company(7, 34000000, 1400, 9999)]
    war = snapshot['active_wars'][0]
    if case == 'minus100_active':
        war['player_relative_war_score'] = -100
    elif case == 'ordinary':
        war['player_relative_war_score'] = -12
    elif case == 'no_major_stakes':
        snapshot['campaign_root_context']['primary_title'] = {'title_id': 9000}
    elif case == 'no_corroboration':
        war.pop('objective_province_states')
    elif case == 'attacker':
        war['player_side'] = 'attacker'
    elif case == 'war_ended':
        snapshot['active_wars'] = []
    elif case == 'weak_reinforcement':
        rows = [company(7, 34000000, 1100, 9999)]
    elif case == 'native_cannot_hire':
        rows[0]['final_terms']['can_hire'] = False
    elif case == 'native_cannot_afford':
        rows[0]['final_terms']['can_afford'] = False
    elif case == 'cash_below_quote':
        snapshot['played_character_gold']['raw'] = 33000000
    elif case == 'incomplete_quote':
        rows[0]['final_terms']['resource_costs_raw'] = [34000000]
    elif case == 'unknown_strength':
        war['enemy_armies'][0]['soldiers'] = None
    elif case == 'hostile_at_spawn':
        war['enemy_armies'][0]['current_province_id'] = 9999
    elif case == 'unknown_pending':
        original = assess(driver)
        pending = employed(driver, original)
        pending['status'] = 'submission_unresolved'
        write_json_atomic(tmp_path / 'war-mercenary-pending-v1.json',
            {'schema': 'xar.war-mercenary-pending.v1', 'pending': pending, 'observed': []})
    def quotes(current, values=None, epoch=1):
        return context(current, rows if values is None else values, epoch)
    async def run():
        baseline = {'phase': 'life_advance', 'selected_step': 'life-advance'}
        with (patch('xar_autoplayer.bridge.service.choose_one_life_turn', return_value=baseline),
              patch('test_war_reinforcement_tradeoff_v1.context', side_effect=quotes),
              patch.object(GameplayBridgeService, '_select_auto_camera_hotspot',
                           return_value={'status': 'unavailable', 'available': False})):
            async with Client(mcp_server.create_server(driver)) as client:
                results = []
                for _ in range(4):
                    result = await client.call_tool('ck3_auto_turn', {})
                    assert not result.is_error
                    results.append(result.structured_content)
                if case in {'success', 'minus100_active'}:
                    assert driver.hire_count == 1
                    hire = next(row for row in results if row['selected_step'] == consumer.HIRE_STEP)
                    selected = hire['plan']['war_mercenary_decision_v1']['selected_candidate']
                    assert selected['emergency_budget_revision_v1']['level'] == 3
                    assert selected['finance']['retains_military_allocation'] is False
                    assert '后续军费可能入债' in hire['plan']['war_decision_presentation_v1']['reason']
                    saved = consumer._ledger(tmp_path)['pending']
                    assert saved['decision']['selected_candidate'] == selected
                    assert hire['result']['payment_verified'] is False
                    assert hire['result']['army_creation_verified'] is False
                else:
                    assert driver.hire_count == 0
                    assert any(row['selected_step'] == 'life-advance' for row in results)
    asyncio.run(run())
