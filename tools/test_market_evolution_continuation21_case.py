"""NoGame software: actual generic prepare/run/verify, metadata joins and old-case isolation.

The authored archive/facts/Native-day ports are not actual SAVE, engine scheduling,
financial, or performance evidence. Production validators and shared phase routes
execute unchanged against these explicitly synthetic documents.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import ck3_mod_acceptance_prepare as preparation
import test_continuous14_clock_diagnostic as prepare_fixture
import test_issuer_refund_toast_case as phase_fixture

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_market_evolution_continuation21.json'


class RetainedRunPort(phase_fixture.RefundRunPort):
    def __init__(self, owner, context, responses):
        super().__init__(owner, context, responses, None)
        self.selection = SimpleNamespace(case={'id': adapter.MARKET_EVOLUTION_CONTINUATION_CASE,
            'normal_close': {'reserve_seconds': 180}})
        self.final_marker = True

    def advance_day(self, **kwargs):
        self.day_calls.append(copy.deepcopy(kwargs))
        self.owner.assertIs(kwargs['allow_event_boundary'], True)
        self.owner.assertEqual(kwargs['pending_interaction_policy'], 'observe_unanswered_inbox')
        before = self.snapshot(); self.date += 24; after = self.snapshot()
        return {'result': {'requested_days': 1, 'requested_interval_complete': True,
            'event_boundary': None, 'before': before, 'after': after, 'elapsed_hours': 24,
            'pending_interaction_observation': {'authored_software_only': True}}}

    def log_bytes(self):
        # The first three once-only markers never recur after cold loading E6.
        if self.final_marker and self.date == self.context['saved_campaign']['date_raw'] + 21 * 24:
            return adapter.MARKET_EVOLUTION_FINAL_MARKER.encode()
        return b''


class MarketEvolutionContinuation21CaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='retained-evolution-software-')
        self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
        self.context = prepare_fixture.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(case=adapter.MARKET_EVOLUTION_CONTINUATION_CASE,
            case_contract=json.loads(CONFIG.read_bytes()), run_id='authored-retained-evolution',
            case_spec={'budgets': {'command_timeout': 300}})
        self.actor = self.context['saved_campaign']['player_id']
        self.source_date = self.context['saved_campaign']['date_raw']
        self.original_raw = self.source_date - 14 * 24
        self.fixture_root = self.root / 'original-java-fixture'; self.fixture_root.mkdir()
        files = {}
        for name in ['descriptor.mod', '_xfma_request.json'] + ['authored-passive-' + str(i) + '.txt' for i in range(10)]:
            p = self.fixture_root / name
            p.write_text('name="Authored software-only fixture"\n' if name == 'descriptor.mod' else
                json.dumps({'schemaVersion': 2, 'caseId': 'market-evolution', 'observationEpoch': 6})
                if name == '_xfma_request.json' else '# Authored software input; never loaded by CK3.\n', encoding='utf-8')
            identity = adapter.pin(p); files[name] = {k: identity[k] for k in ['bytes', 'sha256']}
        self.original_value = {'schema': 'ck3-mod-acceptance-prebuilt-fixture-v1', 'product': 'financial-markets',
            'case_id': 'market-evolution', 'machine_id': 'software-only', 'observed_at_utc': '2026-11-22T00:00:00Z',
            'fixture_root': str(self.fixture_root),
            'producer_source_pins': [adapter.pin(ROOT / 'tools/ck3_mod_acceptance_cases/generic_product_adapter.py')],
            'files': files, 'receipt': {'fixture_contains_business_effects': False,
                'required_product_markers_minimum': {}, 'required_markers': [
                    'XFMAT: TEST PASS market_evolution_observation_ready',
                    'XFMAT: TEST PASS market_evolution_baseline_inventory_captured',
                    'XFMAT: TEST PASS market_evolution_availability_summary_recorded', adapter.MARKET_EVOLUTION_FINAL_MARKER]}}
        self.original = self.put('original.fixture.json', self.original_value)
        self.derived_value = copy.deepcopy(self.original_value)
        self.derived_value['case_id'] = adapter.MARKET_EVOLUTION_CONTINUATION_CASE
        self.derived_value['receipt']['required_markers'] = [adapter.MARKET_EVOLUTION_FINAL_MARKER]
        self.derived = self.put('retained.fixture.json', self.derived_value)
        saved = self.context['saved_campaign']
        self.source = self.archive('source-day14', self.source_date,
            {'path': saved['save'], 'bytes': saved['bytes'], 'sha256': saved['sha256']})
        external = adapter.read_json(self.source['path'])['archive']
        saved.update(save=external['path'], bytes=external['bytes'], sha256=external['sha256'])
        self.source_facts = self.put('source-facts.json', self.facts(14, self.source))
        closed = self.put('closed.json', {'independent_archive_joins': [{'archive_receipt': self.source}],
            'public_run_actual_exit_code': 2, 'public_verify_actual_exit_code': 2})
        self.closed_value = {'actual_public_closed_lease': True, 'actual_state': 'done', 'actual_resources': [],
            'normal_close_qualified': True, 'closure': closed, 'case_acceptance_pass': False}
        self.closed = self.put('released.json', self.closed_value)
        self.context['runtime_manifest'] = self.put('runtime.json', {'machine_id': 'software-only'})
        self.context['case_inputs'].update(prebuilt_fixture_manifest=self.derived,
            market_evolution_continuation={'schema': 'ck3-market-evolution-continuation21-input-v1',
                'source_archive': self.source, 'source_facts': self.source_facts, 'source_closure': self.closed,
                'original_fixture_manifest': self.original, 'observer_native_id': '9999', 'observation_epoch': 6})
        self.responses = {}
        for name, day, requirements in adapter.MARKET_EVOLUTION_CONTINUATION_PHASES:
            checkpoint = self.archive('new-checkpoint-' + str(day), self.source_date + day * 24)
            facts = self.put('new-facts-' + str(day) + '.json', self.facts(14 + day, checkpoint))
            self.responses[name] = {'run_id': self.context['run_id'], 'reviewer': '/root',
                'assertions': {key: True for key in requirements}, 'evidence': [facts]}

    def put(self, name, value):
        p = self.root / name; p.write_text(json.dumps(value), encoding='utf-8'); return adapter.pin(p)

    def archive(self, name, date, payload=None):
        if payload is None:
            p = self.root / (name + '.ck3'); p.write_bytes(('software-only checkpoint ' + name).encode())
            payload = adapter.pin(p)
        external = self.root / (name + '-independent-external.ck3')
        external.write_bytes(Path(payload['path']).read_bytes())
        return self.put(name + '-archive.json', {'schema': 'ck3-financial-checkpoint-archive-v1',
            'machine_id': 'software-only', 'date_raw': date, 'exact_copy': True, 'same_file': False,
            'source': payload, 'archive': adapter.pin(external)})

    def facts(self, cumulative, archive):
        return {'schema': 'market-evolution-raw-facts-unqualified-v2', 'observerNativeId': '9999',
            'request': {'schema': 'market-evolution-raw-interpretation-request-v2',
                'expectedNaturalDays': cumulative, 'observationEpoch': 6,
                'observerManifest': self.original, 'archiveReceipt': archive},
            'days': [{'nativeId': str(1000 + i), 'recordId': [str(i + 1)], 'financialDay': [str(289 + i)],
                'firstScriptDayOrdinal': [str(389640 + i)], 'latestScriptDayOrdinal': [str(389640 + i)],
                'firstNativeRawTicks': [str(self.original_raw + 24 * i)],
                'latestNativeRawTicks': [str(self.original_raw + 24 * i)]} for i in range(cumulative + 1)],
            'issues': [], 'expectedCheckpointContinuityConsistent': True,
            'thirtyFiveDayWindowObserved': cumulative == 35, 'authored_software_only': True}

    def mutate_source(self, change):
        value = adapter.read_json(self.source_facts['path']); change(value)
        self.context['case_inputs']['market_evolution_continuation']['source_facts'] = self.put('mutated-source.json', value)

    def prepared(self):
        return adapter.prepare_case(self.context)

    def test_actual_prepare_preserves_original_twelve_bytes_and_private_engine_cache_boundary(self):
        original_bytes = Path(self.original['path']).read_bytes()
        with patch.object(preparation, '_engine', wraps=preparation._engine) as real_engine:
            result = self.prepared()
        self.assertGreater(real_engine.call_count, 0)
        self.assertEqual(json.loads(json.dumps(result)), result)
        self.assertEqual(result['startup']['mode'], 'saved_campaign')
        profile = Path(result['profile_preparation']['profile']) / 'mod-content/fixture'
        for name, identity in self.original_value['files'].items():
            after = adapter.pin(profile / name)
            self.assertEqual({k: after[k] for k in ['bytes', 'sha256']}, identity)
        compiled, _ = adapter.compiled_contract(self.context)
        self.assertEqual(compiled['required_markers'], [adapter.MARKET_EVOLUTION_FINAL_MARKER])
        self.assertEqual(Path(self.original['path']).read_bytes(), original_bytes)
        self.assertNotIn('_selected_engine', json.dumps(result))

    def test_real_generic_run_phase_protocol_and_verify_keep_local21_distinct_from_original35(self):
        self.prepared(); port = RetainedRunPort(self, self.context, self.responses)
        facts = adapter.run_case(self.context, port)
        self.assertEqual(len(port.day_calls), 21)
        self.assertEqual(port.requests, [row[0] for row in adapter.MARKET_EVOLUTION_CONTINUATION_PHASES])
        self.assertEqual([p['cumulative_day'] for p in facts['market_evolution_continuation_checkpoints']], [14, 30, 35])
        self.assertEqual([p['record_count'] for p in facts['market_evolution_continuation_checkpoints']], [15, 31, 36])
        self.assertTrue(facts['case_contract_qualified']); self.assertFalse(facts['business_pass'])
        self.assertFalse(facts['product_release_pass']); self.assertFalse(facts['financial_daily_coverage_verified'])
        self.assertFalse(facts['original_case_result_upgraded'])
        self.assertTrue(adapter.verify_case(self.context)['case_contract_qualified'])
        self.assertEqual(adapter.read_json(self.closed['path'])['case_acceptance_pass'], False)

    def test_wrong_phase_fresh_ARM_and_changed_calendar_refuse_before_materialization(self):
        for mutate in [lambda c: c['continuation_contract'].update(observer_ARM=True),
                       lambda c: c.update(maximum_natural_days=35),
                       lambda c: c['gui_phases'][1].update(at_day=14)]:
            with self.subTest(mutate=mutate):
                context = copy.deepcopy(self.context); mutate(context['case_contract'])
                with patch.object(preparation, '_engine') as engine, self.assertRaises(ValueError):
                    adapter.prepare_case(context)
                engine.assert_not_called()

    def test_derived_manifest_rejects_rewritten_payload_producer_or_removed_final_assertion(self):
        for key in ['files', 'producer_source_pins', 'required_markers', 'case_id']:
            with self.subTest(key=key):
                context = copy.deepcopy(self.context); changed = copy.deepcopy(self.derived_value)
                if key == 'files': changed['files']['descriptor.mod']['sha256'] = '0' * 64
                elif key == 'producer_source_pins': changed['producer_source_pins'] = []
                elif key == 'required_markers': changed['receipt']['required_markers'] = []
                else: changed['case_id'] = 'market-evolution'
                context['case_inputs']['prebuilt_fixture_manifest'] = self.put('bad-derived-' + key + '.json', changed)
                with self.assertRaises(ValueError): adapter._mec_inputs(context)

    def test_old_R64_savedPair_wrong_epoch_or_observer_and_incomplete_source_are_rejected(self):
        for kind in ['savedPair', 'epoch', 'observer', 'missing']:
            with self.subTest(kind=kind):
                context = copy.deepcopy(self.context)
                if kind == 'savedPair': context['saved_campaign']['date_raw'] -= 14 * 24
                elif kind == 'epoch': context['case_inputs']['market_evolution_continuation']['observation_epoch'] = 7
                elif kind == 'observer': context['case_inputs']['market_evolution_continuation']['observer_native_id'] = '10000'
                else:
                    changed = adapter.read_json(self.source_facts['path']); changed['days'].pop(5)
                    context['case_inputs']['market_evolution_continuation']['source_facts'] = self.put('missing-source.json', changed)
                with self.assertRaises(ValueError): adapter._mec_inputs(context)

    def test_source_partial_case_is_allowed_only_when_actual_normal_close_and_release_are_true(self):
        self.assertEqual(adapter._mec_inputs(self.context)['observation_epoch'], 6)
        for key, bad in [('normal_close_qualified', False), ('actual_state', 'running'), ('actual_resources', ['CK3'])]:
            with self.subTest(key=key):
                context = copy.deepcopy(self.context); row = copy.deepcopy(self.closed_value); row[key] = bad
                context['case_inputs']['market_evolution_continuation']['source_closure'] = self.put('bad-close-' + key + '.json', row)
                with self.assertRaises(ValueError): adapter._mec_inputs(context)

    def test_checkpoint_missing_shifted_duplicate_and_replaced_old_identity_are_not_interpolated(self):
        name = adapter.MARKET_EVOLUTION_CONTINUATION_PHASES[-1][0]
        for kind in ['missing', 'shifted', 'duplicate', 'old_identity', 'wrong_financial']:
            with self.subTest(kind=kind):
                phase = copy.deepcopy(self.responses[name]); row = adapter.read_json(phase['evidence'][0]['path'])
                if kind == 'missing': row['days'].pop(12)
                elif kind == 'shifted': row['days'][20]['firstNativeRawTicks'] = [str(self.original_raw + 21 * 24)]
                elif kind == 'duplicate': row['days'][20]['nativeId'] = row['days'][19]['nativeId']
                elif kind == 'old_identity': row['days'][0]['nativeId'] = '9000'
                else: row['days'][20]['financialDay'] = ['999']
                phase['evidence'] = [self.put('bad-terminal-' + kind + '.json', row)]
                with self.assertRaises(ValueError): adapter._mec_checkpoint(self.context, phase, 21)

    def test_local21_is_not_accepted_as_cumulative21_or_as35_records_without_baseline(self):
        name = adapter.MARKET_EVOLUTION_CONTINUATION_PHASES[-1][0]
        for wrong in [21, 34]:
            phase = copy.deepcopy(self.responses[name])
            archive = adapter.read_json(phase['evidence'][0]['path'])['request']['archiveReceipt']
            phase['evidence'] = [self.put('bad-cumulative-' + str(wrong) + '.json', self.facts(wrong, archive))]
            with self.assertRaises(ValueError): adapter._mec_checkpoint(self.context, phase, 21)

    def test_missing_final_live_marker_never_becomes_pass_from_old_ready_markers(self):
        self.prepared(); port = RetainedRunPort(self, self.context, self.responses); port.final_marker = False
        with self.assertRaisesRegex(ValueError, 'day upper bound'):
            adapter.run_case(self.context, port)
        self.assertEqual(len(port.day_calls), 21)
        self.assertFalse((Path(self.context['output']) / 'generic-product-case-result.json').exists())

    def test_small_ck3_named_metadata_is_refused_before_any_file_read(self):
        disguised = self.put('small.ck3', {'schema': 'authored-json-not-a-SAVE'})
        with patch.object(adapter, 'checked_capture_pin') as read_file:
            with self.assertRaisesRegex(ValueError, 'must be a.json'):
                adapter._mec_json(disguised)
        read_file.assert_not_called()

    def test_archive_same_file_or_noncanonical_alias_is_never_independent(self):
        original = adapter.read_json(self.source['path'])
        for kind in ['same_file', 'same_path', 'relative', 'noncanonical']:
            with self.subTest(kind=kind):
                value = copy.deepcopy(original)
                if kind == 'same_file': value['same_file'] = True
                elif kind == 'same_path': value['source']['path'] = value['archive']['path']
                elif kind == 'relative': value['source']['path'] = 'relative.ck3'
                else:
                    p = Path(value['source']['path'])
                    value['source']['path'] = str(p.parent) + '/./' + p.name
                reference = self.put('bad-independent-' + kind + '.json', value)
                with self.assertRaises(ValueError): adapter._mec_archive(reference, 'software-only')

    def test_source_and_later_checkpoint_archive_must_match_current_runtime_machine(self):
        source = adapter.read_json(self.source['path']); source['machine_id'] = 'other-machine'
        context = copy.deepcopy(self.context)
        context['case_inputs']['market_evolution_continuation']['source_archive'] = self.put('wrong-machine-source.json', source)
        with self.assertRaisesRegex(ValueError, 'another machine'): adapter._mec_inputs(context)
        phase = copy.deepcopy(self.responses[adapter.MARKET_EVOLUTION_CONTINUATION_PHASES[-1][0]])
        facts = adapter.read_json(phase['evidence'][0]['path'])
        receipt = adapter.read_json(facts['request']['archiveReceipt']['path'])
        receipt['machine_id'] = 'other-machine'
        facts['request']['archiveReceipt'] = self.put('wrong-machine-terminal.json', receipt)
        phase['evidence'] = [self.put('wrong-machine-terminal-facts.json', facts)]
        with self.assertRaisesRegex(ValueError, 'another machine'): adapter._mec_checkpoint(self.context, phase, 21)

    def test_original35_case_and_two_old_inbox_case_domains_are_preserved(self):
        original = json.loads((ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_market_evolution.json').read_bytes())
        self.assertEqual([p['at_day'] for p in original['gui_phases']], [0, 14, 30, 35])
        self.assertIn('actual_fresh_market_evolution_epoch_armed_once_via_normal_observer_control_without_product_mutation', original['gui_phases'][0]['requirements'])
        self.assertFalse(adapter._market_evolution_continuation_enabled({'case': 'market-evolution'}))
        for case in ['market-evolution', 'delisting-gui', adapter.MARKET_EVOLUTION_CONTINUATION_CASE]:
            self.assertEqual(adapter._fixture_pending_interaction_policy({'product': 'financial-markets',
                'case_id': case, 'pending_interaction_policy': 'observe_unanswered_inbox'}), 'observe_unanswered_inbox')
        with self.assertRaises(ValueError):
            adapter._fixture_pending_interaction_policy({'product': 'other',
                'case_id': adapter.MARKET_EVOLUTION_CONTINUATION_CASE, 'pending_interaction_policy': 'observe_unanswered_inbox'})


if __name__ == '__main__':
    unittest.main()
