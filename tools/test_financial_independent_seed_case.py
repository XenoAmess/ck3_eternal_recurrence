"""Software-authored seed IO, real generic prepare/CaseClient phase/run/verify.

The historical production contract is replaced only inside each temporary test
with explicitly authored software files. No retained CK3 SAVE is opened, and
none of these assertions grants a real scenario, cash or business qualification.
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
CONFIG = ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_independent_futures_seed.json'


class SoftwarePhasePort(CaseClient):
    """Real root_checkpoint file publication/consumption; only transport authored."""
    def __init__(self, test, context, response):
        self.test, self.context, self.response = test, context, response
        self.output = Path(context['output'])
        self.selection = SimpleNamespace(case={'id': context['case'], 'normal_close': {'reserve_seconds': 180}})
        self.frozen = {'run_id': context['run_id']}
        self.operator_reviewer = '/root'
        self._hold = 9999999999.0
        self.requests = []
        self.frame = {'date_raw': context['saved_campaign']['date_raw'], 'paused': True,
            'played_character': {'character_id': 31254, 'alive': True},
            'active_event': None, 'pending_character_interaction': None}

    def remaining(self):
        return 1800.0

    def guard(self, reserve=90):
        self.test.assertEqual(reserve, 180)
        return {}

    def checkpoint(self, name, value):
        path = self.output / (name + '.json')
        adapter.write_once(path, value)
        if name.endswith('-awaiting'):
            self.requests.append(value)
            # Software Root publisher fixture responds to the actual request.
            self.test.assertEqual(value['required_assertions'], list(adapter.INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS))
            self.test.assertEqual(value['case'], 'independent-futures-seed')
            self.test.assertEqual(value['actual_snapshot'], self.frame)
            adapter.write_once(self.output / (name.removesuffix('-awaiting') + '-root-result.json'), self.response)
        return path

    def snapshot(self, allow_actor_change=False, require_event_free=True):
        self.test.assertFalse(allow_actor_change)
        return copy.deepcopy(self.frame)

    def log_bytes(self):
        return b''

    def advance_day(self, *args, **kwargs):
        raise AssertionError('The independent zero-day seed cannot advance')

    def execute_plan(self, *args, **kwargs):
        raise AssertionError('The independent seed cannot initialize finance or trade')


class IndependentFinancialSeedTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='independent-seed-software-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.context = software_prepare.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.config = json.loads(CONFIG.read_bytes())
        self.source = copy.deepcopy(self.config['independent_seed_contract'])
        saved = self.context['saved_campaign']
        self.source['save'] = {'path': saved['save'], 'bytes': saved['bytes'], 'sha256': saved['sha256']}
        self.source['date_raw'] = saved['date_raw']
        self.wallet = {'schema': 'ck3-captured-actor-wallet-metadata-v1', 'actorNativeId': '31254',
            'nativeDateRaw': saved['date_raw'], 'actorVariables': [{'authored_software_fixture': True}],
            'PRIMARY_source_variable': 'xfm_account', 'PRIMARY_pointer_available': True,
            'PRIMARY_native_reference_when_available': '54'}
        self.source['source_reports'] = {key: self.put('source-' + key + '.json',
            self.wallet if key == 'actor_wallet' else {'authored_software_fixture': key})
            for key in ('archive', 'whole', 'raw', 'actor_wallet')}
        self.config['independent_seed_contract'] = copy.deepcopy(self.source)
        self.context.update(product='financial-markets', case='independent-futures-seed',
            case_contract=self.config, run_id='software-independent-scenario-run',
            case_spec={'budgets': {'command_timeout': 300}})
        self.context['case_inputs']['independent_scenario'] = {
            'scenario_id': 'owned-software-scenario', 'source_run_id': self.source['source_run_id'],
            'source_archive': self.source['source_reports']['archive'], 'mainline_continuation': False,
            'production_recovery': False, 'new_game_claim': False, 'historical_R54_credit': False,
            'replay_existing_orders': []}
        self.addCleanup(patch.stopall)
        patch.object(adapter, 'INDEPENDENT_FINANCIAL_SEED_SOURCE', self.source).start()

    def put(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return adapter.pin(path)

    def response(self):
        date = self.source['date_raw']
        source_path = self.root / 'current-checkpoint-software.ck3'
        source_path.write_bytes(b'authored current software checkpoint')
        archive_path = self.root / 'external-current-software.ck3'
        archive_path.write_bytes(source_path.read_bytes())
        save, source = adapter.pin(archive_path), adapter.pin(source_path)
        receipt = copy.deepcopy(archive_fixture.ACTUAL_R37_ARCHIVE)
        receipt.update(source=source, archive=save, date_raw=date)
        native = receipt['original_checkpoint_result']
        native['checkpoint'].update(path=source['path'], size=source['bytes'], sha256=source['sha256'], date_raw=date)
        baseline = self.put('current-archive.json', receipt)
        whole = self.put('current-whole.json', {'authored_software_fixture': 'whole'})
        raw = self.put('current-raw.json', {'request': {'save': save}, 'fullStreamPasses': 1,
            'inputUnchangedAtGuards': True, 'completeStreamBytes': str(save['bytes']),
            'completeStreamSha256': save['sha256'], 'financialCertified': False})
        endpoint = {'save': save, 'streamingCoverage': {'passes': 2,
            'completeStreamBytes': str(save['bytes']), 'completeStreamSha256': save['sha256']},
            'audit': {'assessment': 'CANDIDATE_INVARIANTS_HOLD'}}
        audit = self.put('current-audit.json', {'audit': {'financial': {'first': endpoint, 'second': [], 'financialCertified': False}},
            'financialCertified': False})
        wallet = copy.deepcopy(self.wallet)
        wallet['request'] = {'archiveReceipt': baseline, 'rawReport': raw}
        wallet_pin = self.put('current-wallet.json', wallet)
        whole_comparison = self.put('whole-comparison.json', {
            'schema': 'ck3-continuous14-whole-financial-news-record-differences-v1',
            'before': self.source['source_reports']['whole'], 'after': whole,
            'before_save': self.source['save'], 'after_save': save, 'dates_raw': [date, date],
            'missing': [], 'added': [], 'changed': [], 'exact_whole_selected_records_equal': True})
        metadata_comparison = self.put('metadata-comparison.json', {
            'schema': 'ck3-continuous14-financial-globals-news-cursor-differences-v1',
            'before': {'report': self.source['source_reports']['raw'], 'save': self.source['save'], 'dateRaw': date},
            'after': {'report': raw, 'save': save, 'dateRaw': date},
            'exactSelectedGlobalAndNewsState': True, 'globalDifferences': [], 'newsDifferences': []})
        details = {'scenario_id': self.context['case_inputs']['independent_scenario']['scenario_id'],
            'source_archive': self.source['source_reports']['archive'], 'physical_archives': [baseline],
            'baseline_archive': baseline, 'audit': audit, 'raw': raw, 'whole': whole,
            'actor_wallet': wallet_pin, 'whole_comparison': whole_comparison, 'metadata_comparison': metadata_comparison}
        return {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {key: True for key in adapter.INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS},
            'evidence': [baseline, audit, raw, whole, wallet_pin, whole_comparison, metadata_comparison],
            'independent_seed': details}

    def run_actual(self, response=None):
        adapter.prepare_case(self.context)
        port = SoftwarePhasePort(self, self.context, self.response() if response is None else response)
        return adapter.run_case(self.context, port), port

    def test_real_saved_prepare_engine_inventory_has_only_passive_carrier_and_empty_plan(self):
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            result = adapter.prepare_case(self.context)
        self.assertGreaterEqual(engine.call_count, 1)
        self.assertEqual(result['startup']['mode'], 'saved_campaign')
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        self.assertEqual(json.loads(Path(result['initial_plan']['path']).read_bytes()), {'steps': []})
        inventory = Path(result['startup']['saved_campaign']['product_inventory'])
        self.assertEqual(json.loads(inventory.read_bytes())['schema'], 'ck3-saved-campaign-profile-inventory-v2')
        profile = Path(result['profile_preparation']['profile'])
        passive = profile / 'mod-content/fixture/common/story_cycles/xfma_independent_financial_seed_passive.txt'
        self.assertEqual(passive.read_text(encoding='utf-8-sig'), ''.join(
            name + ' = { visible = no }\n' for name in self.config['passive_story_types']))
        self.assertFalse(result['business_contract_applicable'])

    def test_actual_caseclient_root_publication_consumption_and_generic_verify_retain_namespace(self):
        response = self.response()
        financial = json.loads(Path(response['independent_seed']['audit']['path']).read_bytes())['audit']['financial']
        self.assertEqual(financial['second'], [])
        self.assertEqual(financial['first']['streamingCoverage']['passes'], 2)
        # The old02 consumer rejects this real DTO at its second-object lookup.
        facts, port = self.run_actual(response)
        self.assertEqual(len(port.requests), 1)
        self.assertEqual(port.requests[0]['reserve_seconds'], 180)
        self.assertEqual(facts['independent_scenario']['scenario_id'], 'owned-software-scenario')
        accepted = json.loads((port.output / 'bind-independent-reproduction-seed-accepted.json').read_bytes())
        self.assertEqual(accepted['independent_seed'], port.response['independent_seed'])
        verified = adapter.verify_case(self.context)
        self.assertTrue(verified['independent_seed_qualified'])
        for key in ('mainline_continuation_credit', 'R54_recovery_or_progress_credit', 'new_game_credit',
                    'business_contract_applicable', 'business_pass', 'product_release_pass'):
            self.assertIs(verified[key], False)
        self.assertNotIn('normal_close_qualified', verified)

    def test_r53_or_different_archive_is_rejected_before_real_profile_or_saved_copy(self):
        self.context['saved_campaign']['sha256'] = 'f' * 64
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            with self.assertRaisesRegex(ValueError, 'pre-order R52'):
                adapter.prepare_case(self.context)
        engine.assert_not_called()
        self.assertFalse((Path(self.context['state_dir']) / 'profile').exists())

    def test_scenario_recovery_replay_or_extra_setup_refuses_before_materialization(self):
        original = copy.deepcopy(self.context)
        for defect in ('production_recovery', 'replay_existing_orders', 'fixture_dir'):
            self.context = copy.deepcopy(original)
            if defect == 'fixture_dir':
                self.context['case_inputs'][defect] = str(self.root)
            else:
                self.context['case_inputs']['independent_scenario'][defect] = [231, 232] if defect == 'replay_existing_orders' else True
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                adapter.prepare_case(self.context)
        self.assertFalse((Path(self.context['state_dir']) / 'profile').exists())

    def test_current_root_false_assertion_cannot_publish_a_seed_success(self):
        response = self.response()
        response['assertions'][adapter.INDEPENDENT_FINANCIAL_SEED_REQUIREMENTS[0]] = False
        with self.assertRaisesRegex(ValueError, 'requirements incomplete'):
            self.run_actual(response)
        self.assertFalse((Path(self.context['output']) / 'generic-product-case-result.json').exists())

    def test_cross_scenario_payload_refuses_even_when_all_root_literals_are_true(self):
        response = self.response()
        response['independent_seed']['scenario_id'] = 'another-software-world'
        with self.assertRaisesRegex(ValueError, 'exact independent source'):
            self.run_actual(response)

    def test_more_than_one_checkpoint_and_changed_whole_graph_do_not_pass(self):
        response = self.response()
        response['independent_seed']['physical_archives'] *= 2
        with self.assertRaisesRegex(ValueError, 'One actual new checkpoint'):
            self.run_actual(response)
        response['independent_seed']['physical_archives'] = [response['independent_seed']['baseline_archive']]
        reference = response['independent_seed']['whole_comparison']
        path = Path(reference['path'])
        comparison = json.loads(path.read_bytes())
        comparison['changed'] = [{'id': '150', 'authored_software_defect': True}]
        path.write_text(json.dumps(comparison), encoding='utf-8')
        replacement = adapter.pin(path)
        response['evidence'] = [replacement if row == reference else row for row in response['evidence']]
        response['independent_seed']['whole_comparison'] = replacement
        compiled, _ = adapter.compiled_contract(self.context)
        port = SoftwarePhasePort(self, self.context, response)
        with self.assertRaisesRegex(ValueError, 'complete financial graph equality'):
            adapter._independent_financial_seed_review(self.context, compiled,
                {'bind-independent-reproduction-seed': response}, port.frame)
        comparison['changed'] = []
        path.write_text(json.dumps(comparison), encoding='utf-8')
        whole_pin = adapter.pin(path)
        response['evidence'] = [whole_pin if row == replacement else row for row in response['evidence']]
        response['independent_seed']['whole_comparison'] = whole_pin
        audit_ref = response['independent_seed']['audit']
        audit_path = Path(audit_ref['path'])
        audit = json.loads(audit_path.read_bytes())
        # The previous authored second-object model is not a real audit DTO.
        audit['audit']['financial']['second'] = copy.deepcopy(audit['audit']['financial']['first'])
        audit_path.write_text(json.dumps(audit), encoding='utf-8')
        audit_pin = adapter.pin(audit_path)
        response['evidence'] = [audit_pin if row == audit_ref else row for row in response['evidence']]
        response['independent_seed']['audit'] = audit_pin
        with self.assertRaisesRegex(ValueError, 'two-pass candidate audit'):
            adapter._independent_financial_seed_review(self.context, compiled,
                {'bind-independent-reproduction-seed': response}, port.frame)

    def test_verify_rechecks_comparator_source_pin_and_never_accepts_late_evidence_replacement(self):
        facts, _ = self.run_actual()
        reference = facts['independent_seed_evidence']['whole_comparison']
        path = Path(reference['path'])
        changed = json.loads(path.read_bytes())
        changed['before'] = facts['independent_seed_evidence']['whole']
        path.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Root evidence changed'):
            adapter.verify_case(self.context)


if __name__ == '__main__':
    unittest.main()
