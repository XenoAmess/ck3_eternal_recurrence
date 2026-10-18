"""Future-only rebel political stakes through existing cache and ordinary MCP."""
import asyncio
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from mcp import Client

from test_war_reinforcement_tradeoff_v1 import WarDriver, company, context
from test_war_emergency_budget_v1 import crisis, spending_for, employed, next_frame
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.environment import write_json_atomic
from xar_autoplayer import war_mercenary_consumer_v1 as consumer
from xar_autoplayer.war_political_survival_stakes_v1 import (
    PROFILE, observe_political_survival_stakes_v1,
)
from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1
from xar_autoplayer.war_strategic_reserve_v1 import assess_mercenary_reinforcement_v1
from xar_autoplayer.war_emergency_budget_v1 import valid_saved_emergency_revision_v1


def test_loaded_modules_bind_the_public_checkout():
    from xar_autoplayer import (
        war_political_survival_stakes_v1, war_emergency_budget_v1,
        war_reinforcement_tradeoff_v1, war_strategic_reserve_v1,
        war_mercenary_consumer_v1,
    )
    source_root = Path(__file__).resolve().parents[2] / 'src' / 'xar_autoplayer'
    records = []
    for module in (war_political_survival_stakes_v1, war_emergency_budget_v1,
                   war_reinforcement_tradeoff_v1, war_strategic_reserve_v1,
                   war_mercenary_consumer_v1):
        actual = Path(module.__file__).resolve()
        expected = (source_root / (module.__name__.split('.')[-1] + '.py')).resolve()
        if actual != expected:
            pytest.fail(f'Qualification imported a different source: {actual} != {expected}')
        records.append({'module': module.__name__, 'path': str(actual),
                        'sha256': hashlib.sha256(actual.read_bytes()).hexdigest()})
    target = os.environ.get('XAR_P87_POLITICAL_LOADED_SOURCES')
    if target:
        Path(target).write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')


def bind_cb(driver):
    snapshot = driver.snapshot
    war = snapshot['active_wars'][0]
    options = {'war_id': war['war_id'], 'source': 'native', 'player_side': war['player_side'],
               'player_is_primary_war_leader': war['player_is_primary_war_leader'],
               'player_relative_war_score': war['player_relative_war_score'],
               'active_casus_belli_present': True,
               'active_casus_belli_identity': {'database_index': 34, 'canonical_key': 'refused_liege_demand_war'},
               'options': {'surrender': {'outcome': 'attacker_defeat'}}}
    owner = SimpleNamespace(_driver_state_lock=RLock(), _war_termination_options={war['war_id']: {
        'options': options, 'query_sequence': snapshot['native_revision'], 'cache_binding': {
            'snapshot_id': snapshot['snapshot_id'], 'native_revision': snapshot['native_revision'],
            'connection_generation': snapshot['diagnostics']['connection_generation'],
            'episode_run_id': snapshot['episode_run_id']}}})
    snapshot['war_termination_options'] = NativeHeadlessGameplayDriver._war_termination_cache_for_snapshot(
        owner, snapshot, episode_run_id=snapshot['episode_run_id'])
    return owner


def rebel(driver):
    snapshot = crisis(driver, level=2)
    snapshot['played_character']['alive'] = True
    snapshot.setdefault('diagnostics', {})['connection_generation'] = 17
    war = snapshot['active_wars'][0]
    war.update(player_side='attacker', targeted_title_ids=[])
    root = snapshot['campaign_root_context']
    root.update(player_character_alive=True, independent=False,
                immediate_liege_character_id=999, top_liege_character_id=999,
                provenance={'game_version': CK3_12004.game_version,
                            'executable_sha256': CK3_12004.executable_sha256,
                            'backend_id': CK3_12004.backend_id('campaign-root-context-v1')})
    root['readiness']['lieges_ready'] = True
    bind_cb(driver)
    return snapshot, war, root


def assess(driver, *, rows=None, ledger=None):
    return assess_mercenary_reinforcement_v1(driver.snapshot,
        context(driver.snapshot, rows or [company(7, 34000000, 1400, 9999)]),
        campaign_root=driver.snapshot['campaign_root_context'], procurement_ledger=ledger,
        spending_observation=spending_for(driver))


def test_native_cache_profile_is_separate_from_title_targets(tmp_path):
    driver = WarDriver(tmp_path)
    snapshot, war, root = rebel(driver)
    profile = observe_political_survival_stakes_v1(snapshot, war, root)
    assert profile['status'] == 'available' and profile['profile'] == PROFILE
    assert profile['observed_liege_relation'] == 'immediate_liege_character_id'
    priority = observe_war_spending_priority_v1(snapshot, campaign_root=root)['wars'][0]
    assert priority['target_stakes_v1']['primary_title_targeted'] is False
    assert priority['target_stakes_v1']['directly_held_target_title_ids'] == []
    selected = assess(driver)['selected_candidate']
    assert selected['emergency_budget_revision_v1']['level'] == 3
    assert selected['crisis_spend_down_v1']['policy'].startswith('political-survival-')
    assert selected['finance']['retains_military_allocation'] is False
    assert selected['crisis_spend_down_v1']['future_funding_credited_raw'] == 0
    assert selected['arrival_eta_days'] is None and selected['battle_win_probability'] is None
    assert profile['actual_penalty_verified'] is False
    root['immediate_liege_character_id'] = 777
    assert observe_political_survival_stakes_v1(snapshot, war, root)['observed_liege_relation'] == 'top_liege_character_id'


@pytest.mark.parametrize('case', ['missing_cb', 'wrong_cb', 'stale_native', 'wrong_connection',
    'wrong_episode', 'not_primary', 'not_liege', 'wrong_build', 'duplicate_query', 'boolean_sequence'])
def test_unqualified_political_inputs_preserve_ordinary_policy(tmp_path, case):
    driver = WarDriver(tmp_path)
    snapshot, war, root = rebel(driver)
    row = snapshot['war_termination_options'][0]
    if case == 'missing_cb':
        snapshot['war_termination_options'] = []
    elif case == 'wrong_cb':
        row['active_casus_belli_identity']['canonical_key'] = 'claim_cb'
    elif case == 'stale_native':
        row['queried_native_revision'] -= 1
    elif case == 'wrong_connection':
        row['queried_connection_generation'] += 1
    elif case == 'wrong_episode':
        row['episode_run_id'] += '-other'
    elif case == 'not_primary':
        war['player_is_primary_war_leader'] = False
    elif case == 'not_liege':
        root['immediate_liege_character_id'] = root['top_liege_character_id'] = 888
    elif case == 'wrong_build':
        root['provenance']['game_version'] = '1.20.0.3'
    elif case == 'duplicate_query':
        snapshot['war_termination_options'].append(deepcopy(row))
    elif case == 'boolean_sequence':
        row['query_sequence'] = True
    assert observe_political_survival_stakes_v1(snapshot, war, root)['status'] == 'unavailable'
    assert assess(driver)['selected_company_id'] is None


def test_production_cb_cache_discards_changed_connection(tmp_path):
    driver = WarDriver(tmp_path)
    snapshot, war, root = rebel(driver)
    owner = bind_cb(driver)
    snapshot['diagnostics']['connection_generation'] += 1
    snapshot['war_termination_options'] = NativeHeadlessGameplayDriver._war_termination_cache_for_snapshot(
        owner, snapshot, episode_run_id=snapshot['episode_run_id'])
    assert snapshot['war_termination_options'] == []
    assert observe_political_survival_stakes_v1(snapshot, war, root)['status'] == 'unavailable'


@pytest.mark.parametrize('case', ['success', 'ordinary_attack', 'no_corroboration', 'no_flip',
                                  'no_flip_retained_buffer', 'below_minus75', 'incomplete_quote', 'unknown_pending'])
def test_registered_ordinary_mcp_keeps_political_guards(tmp_path, case):
    driver = WarDriver(tmp_path)
    snapshot, war, _ = rebel(driver)
    rows = [company(7, 34000000, 1400, 9999)]
    if case == 'ordinary_attack':
        snapshot['war_termination_options'][0]['active_casus_belli_identity']['canonical_key'] = 'claim_cb'
    elif case == 'no_corroboration':
        war.pop('objective_province_states')
    elif case == 'no_flip':
        rows[0]['troop_strength']['current_soldiers'] = 1100
    elif case == 'no_flip_retained_buffer':
        rows = [company(7, 28000000, 1100, 9999)]
    elif case == 'below_minus75':
        war['player_relative_war_score'] = -74
        bind_cb(driver)
    elif case == 'incomplete_quote':
        rows[0]['final_terms']['resource_costs_raw'] = [34000000]
    elif case == 'unknown_pending':
        pending = employed(driver, assess(driver))
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
                results = [(await client.call_tool('ck3_auto_turn', {})).structured_content for _ in range(4)]
                if case == 'success':
                    assert driver.hire_count == 1
                    hire = next(row for row in results if row['selected_step'] == consumer.HIRE_STEP)
                    selected = hire['plan']['war_mercenary_decision_v1']['selected_candidate']
                    assert selected['crisis_spend_down_v1']['political_survival_stakes_v1']['profile'] == PROFILE
                    assert '政治生存危机' in hire['plan']['war_decision_presentation_v1']['reason']
                    assert '并非自动失去全部头衔' in hire['plan']['war_decision_presentation_v1']['reason']
                    assert selected['quoted_resource_costs_raw'] == rows[0]['final_terms']['resource_costs_raw']
                    assert consumer._ledger(tmp_path)['pending'] is not None
                    assert hire['result']['payment_verified'] is False
                else:
                    assert driver.hire_count == 0
                    assert any(row['selected_step'] == 'life-advance' for row in results)
    asyncio.run(run())


def test_political_same_epoch_cannot_reset_cash_or_credit_future_funding(tmp_path):
    driver = WarDriver(tmp_path)
    rebel(driver)
    first = assess(driver)
    receipt = employed(driver, first)
    ledger = {'pending': None, 'observed': [receipt]}
    next_frame(driver)
    bind_cb(driver)
    driver.snapshot['played_character_gold']['raw'] = 20000000
    decision = assess(driver, rows=[company(8, 2000000, 1400, 9999)], ledger=ledger)
    selected = decision['candidates'][0]
    assert decision['selected_company_id'] is None
    assert selected['emergency_budget_revision_v1']['total_package_limit_raw'] == 35000000
    assert selected['procurement_package_budget_v1']['remaining_package_gold_raw'] == 1000000
    forged = deepcopy(receipt)
    forged['decision']['selected_candidate']['emergency_budget_revision_v1']['crisis_spend_down_v1']['future_funding_credited_raw'] = 1
    assert assess(driver, ledger={'pending': None, 'observed': [forged]})['selected_company_id'] is None


def test_saved_political_profile_cannot_lose_its_source_binding(tmp_path):
    driver = WarDriver(tmp_path)
    rebel(driver)
    receipt = employed(driver, assess(driver))
    selected = receipt['decision']['selected_candidate']
    assert valid_saved_emergency_revision_v1(selected, receipt['source_frame'], driver.snapshot) is not None
    selected['emergency_budget_revision_v1']['crisis_spend_down_v1']['political_survival_stakes_v1']['source_frame'] = {}
    assert valid_saved_emergency_revision_v1(selected, receipt['source_frame'], driver.snapshot) is None
