"""Current war cash gate for optional building, upgrade and holding outlays.

The ample-cash numbers are reviewable policy. No refund, loan, new holding
command or prospective income is manufactured by this helper.
"""
from collections.abc import Mapping
from pathlib import Path

from .m5_observed_opportunity_selector import observed_frame

CONSTRUCTION_KINDS = frozenset({'new_building', 'upgrade_building', 'new_holding'})
AMPLE_FIXED_BUFFER_RAW = 40_000_000
AMPLE_MAXIMUM_MAINTENANCE_MONTHS = 24


def observe_war_financing_capability_gap_v1(snapshot, *, priority, construction_ledger, root=None,
        bridge_capabilities=None):
    """Expose an actual capability gap, without queuing a cancel or loan."""
    from .bridge.ingame_decision_outcome_contract import CAPABILITY as confirm_capability
    from .war_reinforcement_tradeoff_v1 import _current_root

    wars = priority.get('wars') if isinstance(priority, Mapping) else None
    active = snapshot.get('active_wars')
    active_ids = {row['war_id'] for row in active if isinstance(row, Mapping)
        and type(row.get('war_id')) is int} if isinstance(active, list) else set()
    wars = [row for row in wars if isinstance(row, Mapping)
        and type(row.get('war_id')) is int and row['war_id'] in active_ids] if isinstance(wars, list) else []
    if not wars:
        return None
    crisis = [row['war_id'] for row in wars if isinstance(row, Mapping)
        and row.get('primary_player_war') is True
        and type(row.get('player_relative_war_score')) is int
        and row['player_relative_war_score'] <= -25
        and (row.get('raised_force_deficit') is True
            or row.get('observed_primary_opponent_objective_occupation_province_ids')
            or row.get('observed_hostile_siege_in_player_subrealm_army_ids')
            or row.get('all_observed_own_raised_armies_currently_retreating') is True)]
    money = snapshot.get('played_character_gold')
    cash = money.get('raw') if (isinstance(money, Mapping) and money.get('scale') == 100000
        and type(money.get('raw')) is int) else None
    maximum = _current_root(snapshot, root).get('player_max_monthly_gold_maintenance_v1')
    value = maximum.get('value') if isinstance(maximum, Mapping) and maximum.get('status') == 'available' else None
    rate = value.get('raw') if isinstance(value, Mapping) and value.get('scale') == 100000 else None
    normal = max(20000000, rate * 18) if type(rate) is int and rate >= 0 else None
    short = type(cash) is int and (cash < normal if normal is not None else cash < 20000000)
    if not crisis and not short:
        return None
    pending = construction_ledger.get('pending') if isinstance(construction_ledger, Mapping) else None
    return {'schema': 'xar.war-financing-capability-gap.v1', 'source_frame': observed_frame(snapshot),
        'trigger': 'cash_shortfall_or_observed_war_crisis', 'crisis_war_ids': crisis,
        'observed_treasury_raw': cash, 'ordinary_military_buffer_raw': normal,
        'maximum_military_maintenance_status': 'same_frame_observed' if normal is not None else 'unobserved',
        'construction_intent_present': isinstance(pending, Mapping),
        'current_active_project_independently_observed': False,
        'cancel_construction': {'status': 'native_interface_missing',
            'reason': 'stock GUI supports cancellation; current .4 adapter has no final CanCancel/refund quote/native receiver',
            'refund_quote_raw': None, 'submit_planned': False},
        'legal_debt': {'status': 'current_build_terms_and_received_funds_unqualified',
            'reason': 'generic selected-decision Confirm exists in source; current .4 full loan terms, typed debt and attributable receipt remain unqualified',
            'source_reviewed_confirm_route': {
                'public_tool': 'ck3_confirm_ingame_decision_outcome_v1',
                'capability': confirm_capability,
                'advertised_in_supplied_bridge_capabilities': (confirm_capability in bridge_capabilities
                    if isinstance(bridge_capabilities, (set, frozenset)) else None),
                'decision_key': 'borrow_from_holy_order_decision',
                'expected_outcome': 'event_window',
                'expected_event_definition_key': 'holy_order.0200',
                'current_selected_legal_decision_verified': False,
                'dispatch_or_expected_event_proves_received_funds': False},
            'current_build_full_terms_verified': False, 'typed_debt_readback_verified': False,
            'independently_attributed_received_funds_verified': False,
            'source_reviewed_debt_commit_option': 'holy_order.0200.a',
            'principal_quote_raw': None, 'submit_planned': False},
        'unreceived_funding_credited_raw': 0, 'selected_action': None,
        'future_funding_receipts_must_keep_same_procurement_epoch': True,
        'unknown_submission_must_not_be_replayed': True,
        'continue_existing_war_action': True}


def observe_wartime_construction_cash_v1(snapshot, *, kind, construction_gold_raw,
        root=None, spending=None, market=None, market_source_frame=None, mercenary_ledger=None,
        procurement_decision=None):
    """Reserve cash after the whole quoted outlay, without changing war actions."""
    result = {'schema': 'xar.wartime-construction-cash.v1', 'construction_kind': kind,
        'source_frame': observed_frame(snapshot), 'new_spend_allowed': False,
        'construction_gold_raw': construction_gold_raw,
        'thresholds_are_user_hard_limits': False, 'thresholds_are_native_rules': False,
        'future_income_credited_raw': 0, 'loan_or_refund_credited_raw': 0,
        'does_not_open_or_refresh_mercenary_procurement_epoch': True}

    def deferred(reason):
        return {**result, 'status': 'defer_optional_construction', 'reason': reason}

    if kind not in CONSTRUCTION_KINDS:
        return deferred('construction_kind_unidentified')
    if kind == 'new_holding':
        return deferred('new_holding_native_action_interface_unavailable')
    wars = snapshot.get('active_wars')
    if not isinstance(wars, list):
        return deferred('current_active_wars_unobserved')
    if not wars:
        return {**result, 'status': 'outside_wartime', 'new_spend_allowed': True}
    if any(not isinstance(war, Mapping) or type(war.get('war_id')) is not int for war in wars):
        return deferred('current_active_wars_unobserved')
    if type(construction_gold_raw) is not int or construction_gold_raw < 0:
        return deferred('complete_current_construction_gold_quote_missing')
    actor = snapshot.get('played_character', {}).get('character_id')
    money = snapshot.get('played_character_gold')
    if (not isinstance(money, Mapping) or type(money.get('raw')) is not int
            or money.get('scale') != 100000):
        return deferred('current_treasury_unobserved')
    if (not isinstance(root, Mapping) or root.get('status') != 'available'
            or root.get('player_character_id') != actor
            or root.get('snapshot_revision') != snapshot.get('native_revision')
            or root.get('date_raw') != snapshot.get('date_raw')):
        return deferred('same_frame_maximum_military_maintenance_unobserved')
    maximum = root.get('player_max_monthly_gold_maintenance_v1')
    value = maximum.get('value') if isinstance(maximum, Mapping) and maximum.get('status') == 'available' else None
    if (not isinstance(value, Mapping) or type(value.get('raw')) is not int
            or value['raw'] < 0 or value.get('scale') != 100000):
        return deferred('same_frame_maximum_military_maintenance_unobserved')
    expected = {'actor_character_id': actor, 'native_revision': snapshot.get('native_revision'),
                'date_raw': snapshot.get('date_raw'), 'snapshot_id': snapshot.get('snapshot_id')}
    budget = spending.get('budget') if isinstance(spending, Mapping) and spending.get('status') == 'observed' else None
    reserved = budget.get('reserved_raw') if isinstance(budget, Mapping) else None
    if (not isinstance(spending, Mapping) or spending.get('frame') != expected
            or not isinstance(reserved, Mapping) or type(reserved.get('gold')) is not int
            or reserved['gold'] < 0 or budget.get('active_war_count') != len(wars)):
        return deferred('same_frame_existing_spending_commitments_unobserved')
    if not isinstance(mercenary_ledger, Mapping) or mercenary_ledger.get('pending') is not None:
        return deferred('mercenary_commitment_unknown_or_pending_never_replay')
    if (not isinstance(market, Mapping) or market.get('available') is not True
            or market.get('actor_character_id') != actor or market.get('date_raw') != snapshot.get('date_raw')
            or market_source_frame != observed_frame(snapshot) or not isinstance(market.get('rows'), list)):
        return deferred('same_frame_available_mercenary_emergency_quotes_unobserved')
    result['market_observation'] = 'complete_empty' if not market['rows'] else 'complete_collection_with_rows'
    if not market['rows']:
        return deferred('complete_market_empty_no_emergency_company')
    hostile_provinces = {row.get('current_province_id') for war in wars
        for row in (war.get('enemy_armies') if isinstance(war.get('enemy_armies'), list) else [])
        if isinstance(row, Mapping) and type(row.get('current_province_id')) is int}
    comparisons = []
    for row in market['rows']:
        if not isinstance(row, Mapping):
            continue
        terms, strength, location, readiness = (row.get(key) for key in
            ('final_terms', 'troop_strength', 'location', 'readiness_v1'))
        if not all(isinstance(item, Mapping) for item in (terms, strength, location, readiness)):
            comparisons.append({'company_id': row.get('company_id'), 'usable': False, 'reason': 'native_terms_incomplete'})
            continue
        costs = terms.get('resource_costs_raw')
        complete = (isinstance(costs, list) and len(costs) == 10
                    and all(type(raw) is int and raw >= 0 for raw in costs)
                    and terms.get('resource_scale') == 100000 and terms.get('available') is True)
        spawn = location.get('hire_auto_raise_province_id')
        usable = (complete and type(row.get('company_id')) is int and row['company_id'] >= 0
            and readiness.get('hire_ready') is True and row.get('employer_id') is None
            and terms.get('can_hire') is True and terms.get('can_afford') is True
            and strength.get('available') is True and type(strength.get('current_soldiers')) is int
            and strength['current_soldiers'] > 0 and type(spawn) is int and spawn > 0
            and location.get('hire_auto_raise_position_ready') is True
            and location.get('hire_auto_raise_attempted_in_active_war') is True and spawn not in hostile_provinces)
        comparisons.append({'company_id': row.get('company_id'), 'usable': usable,
            'contract_gold_raw': costs[0] if complete else None,
            'current_soldiers': strength.get('current_soldiers'),
            'reason': 'current_native_legal_emergency_cash_buffer_quote' if usable else 'native_legal_strength_or_spawn_terms_not_ready'})
    result['mercenary_quote_comparisons'] = comparisons
    options = [row for row in comparisons if row['usable']]
    if not options:
        return deferred('no_current_native_usable_emergency_company_quote')
    from .war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1

    priority = observe_war_spending_priority_v1(snapshot, campaign_root=root)
    order = priority['cash_protection_priority_war_ids']
    focus = next((war for identity in order for war in priority['wars'] if war['war_id'] == identity), None)
    own = focus.get('observed_player_raised_soldiers') if focus else None
    enemy = focus.get('observed_enemy_raised_soldiers') if focus else None
    deficit = max(0, enemy - own) if type(own) is int and type(enemy) is int else None
    adequate = [row for row in options if type(deficit) is int and deficit > 0 and row['current_soldiers'] >= deficit]
    selected = procurement_decision.get('selected_candidate') if isinstance(procurement_decision, Mapping) else None
    approved = None
    if isinstance(selected, Mapping) and selected.get('rejection_reasons') == []:
        finance = selected.get('finance')
        finance_frame = finance.get('source_frame') if isinstance(finance, Mapping) else None
        expected_finance_frame = {'actor_character_id': actor, 'native_revision': snapshot.get('native_revision'),
                                  'date_raw': snapshot.get('date_raw')}
        if (finance_frame == expected_finance_frame and focus
                and isinstance(selected.get('purpose_war_ids'), list)
                and focus['war_id'] in selected['purpose_war_ids']):
            approved = next((row for row in options if row['company_id'] == selected.get('company_id')
                and row['contract_gold_raw'] == selected.get('gold_cost_raw')
                and type(deficit) is int and row['current_soldiers'] >= deficit), None)
    if approved:
        chosen, basis = approved, 'current_frame_assessed_suitable_procurement_quote'
    elif adequate:
        chosen = min(adequate, key=lambda row: (row['contract_gold_raw'], row['company_id']))
        basis = 'cheapest_current_legal_quote_covering_focused_observed_headcount_deficit'
    else:
        chosen = max(options, key=lambda row: (row['contract_gold_raw'], row['company_id']))
        basis = 'conservative_maximum_complete_native_legal_quote_not_a_win_or_arrival_forecast'
    military = max(AMPLE_FIXED_BUFFER_RAW, value['raw'] * AMPLE_MAXIMUM_MAINTENANCE_MONTHS)
    required = military + reserved['gold'] + chosen['contract_gold_raw']
    after = money['raw'] - construction_gold_raw
    return {**result, 'status': 'ample_wartime_cash' if after >= required else 'defer_optional_construction',
        'reason': 'retain_maximum_military_commitments_and_native_emergency_quote' if after >= required else 'wartime_cash_not_very_ample_after_optional_outlay',
        'new_spend_allowed': after >= required, 'observed_treasury_raw': money['raw'],
        'gold_after_construction_raw': after, 'required_remaining_gold_raw': required,
        'maximum_monthly_military_raw': value['raw'], 'maintenance_policy_months': AMPLE_MAXIMUM_MAINTENANCE_MONTHS,
        'fixed_buffer_policy_gold_raw': AMPLE_FIXED_BUFFER_RAW, 'military_buffer_raw': military,
        'existing_unpaid_commitments_raw': reserved['gold'], 'emergency_company_quote': chosen,
        'emergency_quote_reserve_policy': basis, 'focused_war_id': focus.get('war_id') if focus else None,
        'observed_focused_headcount_deficit': deficit,
        'arrival_eta_days': None, 'battle_win_probability': None,
        'quoted_company_arrival_or_combat_usefulness_verified': False,
        'paid_contracts_already_reflected_in_current_wallet_not_deducted_twice': True}


def observe_driver_wartime_construction_cash_v1(driver, snapshot, *, kind, construction_gold_raw, history=None,
        procurement_decision=None):
    """Reuse existing local current inputs; perform zero Native queries."""
    from .activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1
    from .strategy import _same_frame_campaign_root_context
    from .war_mercenary_consumer_v1 import _context_with_reference, _ledger

    history = history if isinstance(history, list) else snapshot.get('native_command_history', [])
    history = history if isinstance(history, list) else []
    root = _same_frame_campaign_root_context(history, dict(snapshot))
    market, reference = _context_with_reference(history, snapshot)
    directory = getattr(driver, 'state_dir', None)
    frame = observed_frame(snapshot)
    spending = None
    ledger = None
    if isinstance(directory, Path):
        spending = observe_feast_start_budget_v1(snapshot, {
            'actor_character_id': frame['played_character_id'], 'snapshot_revision': frame['native_revision'],
            'date_raw': frame['date_raw'], 'post_snapshot_id': frame['snapshot_id'],
            'queried_revision': frame['revision']}, state_dir=directory, campaign_root=root)
        ledger = _ledger(directory)
    return observe_wartime_construction_cash_v1(snapshot, kind=kind, construction_gold_raw=construction_gold_raw,
        root=root, spending=spending, market=market,
        market_source_frame=reference.get('source_frame') if isinstance(reference, Mapping) else None,
        mercenary_ledger=ledger, procurement_decision=procurement_decision)
