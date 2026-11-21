"""Real generic/public saved prepare and Root file protocol; software IO only.

All financial reports, decisions and checkpoint contents here are explicitly
authored transport fixtures. No Game, real trade, receipt parser or finance
execution/qualification is claimed by these acceptance-consumer regressions.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_prepare as preparation
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import test_continuous14_clock_diagnostic as software_prepare
import test_futures_gui_transactions_case as archive_fixture

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_coin_campaign_gui.json'


class CampaignPort(CaseClient):
    def __init__(self, owner, context, responses):
        self.owner, self.context, self.responses = owner, context, responses
        self.output = Path(context['output'])
        self.selection = SimpleNamespace(case={'id': context['case'], 'normal_close': {'reserve_seconds': 180}})
        self.frozen = {'run_id': context['run_id']}; self.operator_reviewer = '/root'
        self._hold = 9999999999.0; self.requests = []; self.day_shift = False

    def remaining(self): return 1800.0

    def guard(self, reserve=90):
        self.owner.assertEqual(reserve, 180)
        return {}

    def checkpoint(self, name, value):
        path = self.output / (name + '.json')
        adapter.write_once(path, value)
        if name.endswith('-awaiting'):
            phase = name.removesuffix('-awaiting'); self.requests.append(phase)
            self.owner.assertEqual(value['case'], 'coin-campaign-gui')
            adapter.write_once(self.output / (phase + '-root-result.json'), self.responses[phase])
        return path

    def snapshot(self, allow_actor_change=False, require_event_free=True):
        self.owner.assertFalse(allow_actor_change)
        date = self.context['saved_campaign']['date_raw'] + (24 if self.day_shift and self.requests else 0)
        return {'date_raw': date, 'paused': True, 'played_character': {'character_id': 31254, 'alive': True},
            'active_event': None, 'pending_character_interaction': None}

    def log_bytes(self): return b''

    def advance_day(self, *args, **kwargs):
        raise AssertionError('The campaign case must not advance or ARM')

    def execute_plan(self, *args, **kwargs):
        raise AssertionError('The adapter must not submit GUI or financial setters')


class CoinCampaignGuiCaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='campaign-consumer-software-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        self.context = software_prepare.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(product='financial-markets', case='coin-campaign-gui',
            case_contract=json.loads(CONFIG.read_bytes()), run_id='authored-campaign-run',
            case_spec={'budgets': {'command_timeout': 300}})
        saved = self.context['saved_campaign']; save = {k: saved[v] for k, v in
            [('path', 'save'), ('bytes', 'bytes'), ('sha256', 'sha256')]}
        source = self.put('source-archive.json', {'schema': 'ck3-financial-checkpoint-archive-v1',
            'exact_copy': True, 'same_file': False, 'date_raw': saved['date_raw'], 'archive': save})
        self.binding = {'source_archive': source, 'scenario_id': 'authored-independent-campaign',
            'coin_a': {'native_id': '71', 'permanent_id': '11', 'entity_type': 3},
            'coin_b': {'native_id': '72', 'permanent_id': '12', 'entity_type': 4}}
        self.context['case_inputs']['coin_campaign'] = self.binding
        self.baseline = self.archive('baseline'); self.paid = self.archive('paid'); self.terminal = self.archive('terminal')
        self.note = self.put('authored-metadata-only.json', {'software_fixture_no_Game_proof': True})
        self.action = {'query': self.note, 'activation': self.note}
        self.account = {'native_id': '54', 'permanent_id': '2', 'holder_character_id': '31254'}
        self.baseline_bindings = {**copy.deepcopy(self.binding), 'PRIMARY': self.account}
        self.cells = self.positive_cells()
        self.responses = self.phase_responses()

    def put(self, name, value):
        path = self.root / name; path.write_text(json.dumps(value), encoding='utf-8')
        return adapter.pin(path)

    def archive(self, name):
        source = self.root / (name + '-source.ck3'); saved = self.root / (name + '-external.ck3')
        source.write_bytes(('authored fixture checkpoint ' + name).encode()); saved.write_bytes(source.read_bytes())
        receipt = copy.deepcopy(archive_fixture.ACTUAL_R37_ARCHIVE)
        receipt.update(source=adapter.pin(source), archive=adapter.pin(saved), date_raw=self.context['saved_campaign']['date_raw'])
        pin = adapter.pin(source)
        receipt['original_checkpoint_result']['checkpoint'].update(
            path=pin['path'], size=pin['bytes'], sha256=pin['sha256'], date_raw=receipt['date_raw'])
        return self.put(name + '-archive.json', receipt)

    def positive_cells(self):
        result = {}
        for name, role in zip(adapter.COIN_CAMPAIGN_CELLS[:2], ('coin_a', 'coin_b')):
            assertions = ['actual_typed_bound_entity_reference_preserved',
                'actual_independent_named_entity_source_corroborates_reference',
                'actual_source_and_current_coin_permanent_identity_and_entity_binding_match']
            result[name] = {'status': 'OBSERVED', 'coin_role': role,
                # Explicit software type stimulus, not an asserted real SaveCore enum.
                'entity_reference': {'serialized_type': 'authored_entity', 'identity': 'software-entity-' + role},
                'named_entity_source': self.note, 'assertions': {key: True for key in assertions},
                'audit': self.note, 'raw': self.note}
        common = ['actual_normal_fresh_GUI_only_no_unknown_replay', 'actual_current_PRIMARY_not_restricted_money',
            'actual_independent_cash_coin_fee_and_all_old_obligations_reconciled']
        promotion = ['actual_frozen_A_payer_controller_nonce_charter_event_once',
            'actual_PRIMARY_100cent_fee_and_A_advertising_plus100_B_unchanged',
            'actual_no_price_or_recipient_delivery_credit_from_ad_reached']
        result['paid_A_charter_promotion'] = {'status': 'OBSERVED', 'assertions': {key: True for key in common + promotion},
            'before_archive': self.baseline, 'after_archive': self.paid, 'gui_actions': [self.action],
            'audit': self.note, 'raw': self.note, 'reconciliation': self.note, 'paid_cents': 100,
            'route': 'xfm_market_charter/xfm_issuer.100/xfm_issuer_promote'}
        trades = []
        for index, (role, side) in enumerate((('coin_a', 'BUY'), ('coin_b', 'BUY'), ('coin_a', 'SELL'), ('coin_b', 'SELL'))):
            coin = self.binding[role]
            trades.append({'coin_role': role, 'side': side, 'coin_native_id': coin['native_id'],
                'coin_id': coin['permanent_id'], 'order_native_id': str(1000 + index), 'order_id': str(20 + index),
                'requested_lots': 1, 'filled_units': '1', 'gross_cents': '100', 'fee_cents': '1',
                'counterparty_account_native_id': '81', 'counterparty_beneficial_owner_id': '82',
                'gui_actions': [self.action], 'execution_reconciliation': self.note})
        assertions = common + ['actual_four_new_A_B_buy_sell_fills_not_submission_or_quotes',
            'actual_coin_switch_each_order_uses_selected_asset_only_and_distinct_beneficiary']
        result['two_coin_same_day_buy_sell_isolation'] = {'status': 'OBSERVED',
            'assertions': {key: True for key in assertions}, 'before_archive': self.paid,
            'after_archive': self.terminal, 'gui_actions': [self.action], 'audit': self.note, 'raw': self.note,
            'reconciliation': self.note, 'trades': trades}
        return result

    def phase_responses(self):
        evidence = [self.baseline, self.paid, self.terminal, self.note]
        phases = {name: {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {key: True for key in required}, 'evidence': evidence}
            for name, required in adapter.COIN_CAMPAIGN_PHASES}
        phases[adapter.COIN_CAMPAIGN_PHASES[0][0]].update(baseline_archive=self.baseline,
            baseline_audit=self.note, baseline_raw=self.note, baseline_whole=self.note,
            campaign_bindings=self.baseline_bindings)
        phases[adapter.COIN_CAMPAIGN_PHASES[1][0]].update(
            physical_archives=[self.baseline, self.paid, self.terminal], coin_campaign_gui=self.cells)
        return phases

    def review(self):
        context = adapter.resolve_post_start(self.context)
        return adapter._coin_campaign_review(context, {'config': context['case_contract']},
            self.responses, self.context['saved_campaign']['date_raw'])

    def test_actual_saved_prepare_private_engine_inventory_passive_catalog_and_empty_plan(self):
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            result = adapter.prepare_case(self.context)
        self.assertGreaterEqual(engine.call_count, 1)
        self.assertEqual(result['startup']['mode'], 'saved_campaign')
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        self.assertEqual(json.loads(Path(result['initial_plan']['path']).read_bytes()), {'steps': []})
        profile = Path(result['profile_preparation']['profile'])
        passive = profile / 'mod-content/fixture/common/story_cycles/xfma_coin_campaign_passive.txt'
        self.assertEqual(passive.read_text(encoding='utf-8-sig'), ''.join(
            name + ' = { visible = no }\n' for name in self.context['case_contract']['passive_story_types']))
        self.assertEqual(json.loads(Path(result['startup']['saved_campaign']['product_inventory']).read_bytes())['schema'],
            'ck3-saved-campaign-profile-inventory-v2')

    def test_actual_CaseClient_Root_file_protocol_runs_two_phases_and_verify_retains_only_local_credit(self):
        adapter.prepare_case(self.context)
        port = CampaignPort(self, self.context, self.responses)
        facts = adapter.run_case(self.context, port)
        self.assertEqual(port.requests, [name for name, _ in adapter.COIN_CAMPAIGN_PHASES])
        accepted = json.loads((port.output / (port.requests[1] + '-accepted.json')).read_bytes())
        self.assertEqual(accepted['coin_campaign_gui'], self.cells)
        self.assertTrue(facts['case_contract_qualified'])
        verified = adapter.verify_case(self.context)
        self.assertEqual(verified['observed_cells'], list(adapter.COIN_CAMPAIGN_CELLS))
        for key in ('business_pass', 'product_release_pass', 'global_news_delivery_pass',
                    'manipulation_causal_success_pass', 'financial_daily_coverage_verified', 'performance_pass'):
            self.assertIs(verified[key], False)
        self.assertNotIn('normal_close_qualified', verified)
        Path(self.note['path']).write_text('changed retained evidence', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Root evidence changed'):
            adapter.verify_case(self.context)

    def test_unfilled_or_unavailable_cells_stay_PARTIAL_without_advance_or_fill_credit(self):
        for name in list(self.cells):
            self.cells[name] = {'status': 'NOT_OBSERVED', 'reason': 'Authored unavailable/never-filled transport', 'evidence': []}
        adapter.prepare_case(self.context)
        facts = adapter.run_case(self.context, CampaignPort(self, self.context, self.responses))
        self.assertFalse(facts['case_contract_qualified']); self.assertEqual(facts['status'], 'PARTIAL')
        self.assertEqual(facts['observed_cells'], [])
        self.assertEqual(adapter.verify_case(self.context)['not_observed_cells'], list(adapter.COIN_CAMPAIGN_CELLS))

    def test_same_coin_wrong_entity_role_or_source_rejected_before_engine_profile(self):
        original = copy.deepcopy(self.context)
        for defect in ('same', 'type', 'source'):
            self.context = copy.deepcopy(original)
            binding = self.context['case_inputs']['coin_campaign']
            if defect == 'same': binding['coin_b']['native_id'] = binding['coin_a']['native_id']
            elif defect == 'type': binding['coin_b']['entity_type'] = 3
            else: self.context['saved_campaign']['sha256'] = 'f' * 64
            with self.subTest(defect=defect), patch.object(preparation, '_engine') as engine:
                with self.assertRaises(ValueError): adapter.prepare_case(self.context)
                engine.assert_not_called()
        self.assertFalse((Path(self.context['state_dir']) / 'profile').exists())

    def test_direct_issuer_button_wrong_fee_or_root_false_cannot_be_paid_charter(self):
        cell = self.cells['paid_A_charter_promotion']; original = copy.deepcopy(cell)
        for defect in ('route', 'fee', 'assertion'):
            cell.clear(); cell.update(copy.deepcopy(original))
            if defect == 'route': cell['route'] = 'xfm_market_promote'
            elif defect == 'fee': cell['paid_cents'] = 99
            else: cell['assertions']['actual_PRIMARY_100cent_fee_and_A_advertising_plus100_B_unchanged'] = False
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_order_ACK_zero_fill_duplicate_wrong_coin_and_self_beneficiary_do_not_pass(self):
        trades = self.cells['two_coin_same_day_buy_sell_isolation']['trades']; original = copy.deepcopy(trades)
        for defect in ('zero-fill', 'duplicate', 'wrong-coin', 'self'):
            trades[:] = copy.deepcopy(original)
            if defect == 'zero-fill': trades[0]['filled_units'] = '0'
            elif defect == 'duplicate': trades[1]['order_id'] = trades[0]['order_id']
            elif defect == 'wrong-coin': trades[1]['coin_native_id'] = self.binding['coin_a']['native_id']
            else: trades[0]['counterparty_beneficial_owner_id'] = '31254'
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_missing_entity_type_or_named_source_is_not_inferred_from_coin_label(self):
        cell = self.cells['title_binding_readback']; original = copy.deepcopy(cell)
        for defect in ('unknown', 'missing-source'):
            cell.clear(); cell.update(copy.deepcopy(original))
            if defect == 'unknown': cell['entity_reference']['serialized_type'] = 'unknown'
            else: cell.pop('named_entity_source')
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_archive_alias_fourth_SAVE_or_skipped_promotion_endpoint_rejected(self):
        phase = self.responses[adapter.COIN_CAMPAIGN_PHASES[1][0]]
        original = copy.deepcopy(phase['physical_archives'])
        for defect in ('alias', 'fourth', 'skip-paid'):
            phase['physical_archives'] = copy.deepcopy(original)
            if defect == 'alias': phase['physical_archives'][2] = phase['physical_archives'][1]
            elif defect == 'fourth': phase['physical_archives'].append(self.baseline)
            else: self.cells['two_coin_same_day_buy_sell_isolation']['before_archive'] = self.baseline
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_corrupt_day_bound_or_synthetic_input_rejected_before_materialization(self):
        original = copy.deepcopy(self.context)
        for defect in ('days', 'setters'):
            self.context = copy.deepcopy(original)
            if defect == 'days': self.context['case_contract']['maximum_natural_days'] = True
            else: self.context['case_inputs']['fixture_dir'] = str(self.root)
            with self.subTest(defect=defect), patch.object(preparation, '_engine') as engine:
                with self.assertRaises(ValueError): adapter.prepare_case(self.context)
                engine.assert_not_called()

    def test_actual_run_day_shift_remains_rejected(self):
        adapter.prepare_case(self.context)
        port = CampaignPort(self, self.context, self.responses); port.day_shift = True
        with self.assertRaisesRegex(ValueError, 'calendar bound'): adapter.run_case(self.context, port)


if __name__ == '__main__':
    unittest.main()
