"""Actual public generic/CaseClient consumers, authored software metadata only.

These temporary files are NOT CK3 saves, real fees/refunds, actual Java reader
outputs or Native delivery. The tests execute production validation and public
day composition; ports replace only Game/queue/SDK boundaries. No live credit.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_client as client_module
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import test_continuous14_clock_diagnostic as software_prepare
import test_futures_gui_transactions_case as archive_fixture

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_issuer_refund_toast.json'
EXE = '2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC'


class CapturePort(CaseClient):
    """Execute the real advance_day; only the queued SDK/clock boundary is a port."""
    def __init__(self, owner, context):
        self.owner, self.context = owner, context
        self.actor = owner.actor
        self.output = Path(context['output']); self.output.mkdir(exist_ok=True, parents=True)
        self.selection = SimpleNamespace(adapter_context=lambda: context,
            case={'id': 'issuer-refund-toast', 'normal_close': {'reserve_seconds': 180}})
        self.manifest = {'game': {'version': '1.21.0'}}
        self._process = {'pid': 999, 'birth_filetime_100ns': '123'}
        self.frozen = {'run_id': context['run_id']}; self._seq = 0
        self.calls = []; self.reserves = []; self.date = context['saved_campaign']['date_raw']
        self._binding = None

    def guard(self, reserve=90, **kwargs):
        self.reserves.append(reserve); return {'steps': []}
    def remaining(self): return 3600.0
    def validate_frame(self, frame, **kwargs):
        self.owner.assertIsInstance(frame, dict); return frame
    def snapshot(self, **kwargs): return self.full(self.date)

    def full(self, date):
        return {'date_raw': date, 'paused': True, 'active_event': None,
            'pending_character_interaction': None,
            'played_character': {'character_id': self.actor, 'alive': True},
            'diagnostics': {'bridge_pid': 999, 'connection_generation': 7}}

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        self.calls.append(copy.deepcopy(steps)); self.reserves.append(reserve)
        before = self.full(self.date); self.date += 24; after = self.full(self.date)
        rows = [{'id': steps[0]['id'], 'plan': copy.deepcopy(steps[0]), 'ok': True,
            'finished_at': 'authored-software-time', 'error': None, 'after_snapshot': after,
            'result': {'requested_days': 1, 'requested_interval_complete': True,
                       'event_boundary': None, 'before': before, 'after': after, 'elapsed_hours': 24}}]
        for index, step in enumerate(steps[1:], 1):
            dto = {'schema': 'ck3_1210_current_interface_toast_result_v1',
                'step': 'query-current-interface-toast-v1', 'game_version': '1.21.0',
                'executable_sha256': EXE, 'read_only': True, 'effect_attempted': False,
                'status': 'available', 'accepted': True, 'snapshot_id': 'native:1', 'native_revision': '1',
                'public_revision': '1', 'connection_generation': '7', 'query_sequence': str(index),
                'owner_thread_id': 5, 'completed_application_frame': str(99 + index), 'game_pid': 999,
                'viewer_played_character_id': self.actor, 'date_raw': self.date, 'queue_count': 1,
                'title': 'Authored software title', 'description': 'Authored software message',
                'application_main_observed': True, 'full_snapshot_before_verified': True,
                'full_snapshot_after_verified': True, 'source_abi_pins_verified': True,
                'adapter_id': 'ck3-1.21.0-msvc-x64', 'backend': 'ck3-1.21.0-native-headless-main-thread',
                'recipient_identity_available': False, 'news_origin_available': False, 'delivery_confirmed': False,
                'unavailable_reason': None,
                'saved_gui_scopes': [{'name': n, 'kind': kind, 'observed_tag': tag,
                    'identity_available': True, 'identity': value, 'unavailable_reason': None}
                    for n, kind, tag, value in [('xfm_news_recipient', 'character', 4, str(self.actor)),
                        ('xfm_news_display_entry', 'story', 22, '90'), ('xfm_news_actor', 'character', 4, str(self.actor))]],
                'saved_script_scopes': [],
                'stage': 'visible_pending_frame' if index == 1 else 'visible'}
            rows.append({'id': step['id'], 'plan': copy.deepcopy(step), 'ok': True,
                'finished_at': 'authored-software-time', 'error': None,
                'result': dto, 'after_snapshot': after})
        (self.output / 'plans').mkdir(exist_ok=True)
        adapter.write_once(self.output / 'plans' / (name + '.json'), {'steps': steps})
        adapter.write_once(self.output / (name + '.actual-results.json'), {'rows': rows, 'business_PASS_inferred': False})
        return rows


class RefundRunPort(CaseClient):
    """The real public Root response protocol; no GUI/financial action occurs."""
    def __init__(self, owner, context, responses, capture):
        self.owner, self.context, self.responses, self.capture = owner, context, responses, capture
        self.actor = owner.actor
        self.output = Path(context['output']); self.selection = SimpleNamespace(
            case={'id': 'issuer-refund-toast', 'normal_close': {'reserve_seconds': 180}})
        self.frozen = {'run_id': context['run_id']}; self.operator_reviewer = '/root'
        self._hold = 9999999999.0; self._process = {'pid': 999}; self.requests = []; self.day_calls = []
        self.date = context['saved_campaign']['date_raw']

    def remaining(self): return 3600.0
    def guard(self, reserve=90, **kwargs):
        self.owner.assertEqual(reserve, 180); return {}
    def snapshot(self, allow_actor_change=False, require_event_free=True):
        self.owner.assertFalse(allow_actor_change)
        return {'date_raw': self.date, 'paused': True, 'active_event': None,
            'pending_character_interaction': None,
            'played_character': {'character_id': self.actor, 'alive': True}}
    def log_bytes(self): return b''
    def checkpoint(self, name, value):
        path = self.output / (name + '.json'); adapter.write_once(path, value)
        if name.endswith('-awaiting'):
            phase = name.removesuffix('-awaiting'); self.requests.append(phase)
            adapter.write_once(self.output / (phase + '-root-result.json'), self.responses[phase])
        return path
    def advance_day(self, **kwargs):
        self.day_calls.append(kwargs)
        self.owner.assertIs(kwargs.get('current_toast_queries'), True)
        before = self.snapshot(); self.date += 24; after = self.snapshot()
        return {'result': {'requested_days': 1, 'requested_interval_complete': True,
            'event_boundary': None, 'before': before, 'after': after, 'elapsed_hours': 24},
            'current_toast_capture': self.capture}
    def execute_plan(self, *args, **kwargs):
        raise AssertionError('Generic must use the existing public day method, not a parallel clock/GUI driver')


class IssuerRefundToastCaseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='issuer-refund-toast-software-')
        self.addCleanup(temp.cleanup); self.root = Path(temp.name)
        self.context = software_prepare.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(product='financial-markets', case='issuer-refund-toast',
            case_contract=json.loads(CONFIG.read_bytes()), run_id='authored-issuer-refund-toast',
            case_spec={'budgets': {'command_timeout': 300}})
        saved = self.context['saved_campaign']; self.date = saved['date_raw']
        self.actor = saved['player_id']
        save = {k: saved[v] for k, v in [('path', 'save'), ('bytes', 'bytes'), ('sha256', 'sha256')]}
        self.source = self.put('source-archive.json', {'schema': 'ck3-financial-checkpoint-archive-v1',
            'machine_id': 'software-machine', 'exact_copy': True, 'same_file': False,
            'date_raw': self.date, 'archive': save})
        self.context['case_inputs']['issuer_refund_toast'] = {'source_archive': self.source,
            'scenario_id': 'authored-software-refund'}
        self.note = self.put('authored-no-Game-evidence.json', {'software_only': True})
        self.base = self.archive('before', self.date); self.refunded = self.archive('refunded', self.date)
        self.terminal = self.archive('post-query', self.date + 24)
        self.responses = self.phases()
        self.capture = None

    def put(self, name, value):
        path = self.root / name; path.write_text(json.dumps(value), encoding='utf-8')
        return adapter.pin(path)
    def archive(self, name, date):
        source, target = self.root / (name + '-source.ck3'), self.root / (name + '-external.ck3')
        source.write_bytes(('authored software checkpoint ' + name).encode()); target.write_bytes(source.read_bytes())
        receipt = copy.deepcopy(archive_fixture.ACTUAL_R37_ARCHIVE)
        receipt.update(machine_id='software-machine', source=adapter.pin(source), archive=adapter.pin(target), date_raw=date)
        actual = adapter.pin(source)
        receipt['original_checkpoint_result']['checkpoint'].update(path=actual['path'],
            size=actual['bytes'], sha256=actual['sha256'], date_raw=date)
        return self.put(name + '-archive.json', receipt)
    def phase(self, index, **extras):
        requirements = adapter.ISSUER_REFUND_TOAST_PHASES[index][2]
        return {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {key: True for key in requirements}, 'evidence': [], **extras}

    def phases(self):
        primary = {'native_id': '54', 'permanent_id': '2', 'holder_character_id': str(self.actor),
                   'free_cents': '1000', 'reserved_cents': '7'}
        baseline = self.phase(0, source_archive=self.source, baseline_archive=self.base,
            baseline_audit=self.note, baseline_raw=self.note, baseline_whole=self.note,
            eligibility={'status': 'OBSERVED', 'PRIMARY': primary, 'checks': {
                'adult_living_human': True, 'PRIMARY_legal_unfrozen': True,
                'normal_company_micro_registration_enabled': True,
                'no_pending_offer_or_issue_cooldown': True, 'no_business_setters': True}, 'evidence': [self.note]})
        issue = {'xfm_issue_receipt_version': '1', 'xfm_issue_receipt_coin_id': '94',
            'xfm_issue_receipt_actor': str(self.actor), 'xfm_issue_receipt_payer': '54', 'xfm_issue_receipt_payer_id': '2',
            'xfm_issue_receipt_day': '247', 'xfm_issue_receipt_is_ai': '0', 'xfm_issue_receipt_fee_cents': '100',
            'xfm_issue_receipt_free_before': '1000', 'xfm_issue_receipt_free_pre_fee': '1000',
            'xfm_issue_receipt_free_after': '900', 'xfm_issue_receipt_reserved_before': '7',
            'xfm_issue_receipt_reserved_after': '7', 'xfm_issue_receipt_fees_before': '42',
            'xfm_issue_receipt_fees_after': '142', 'xfm_issue_receipt_topup_cents': '0'}
        coin = {'native_id': '70', 'xfm_coin_id': '94', 'xfm_entity_type': '6', 'xfm_controller': str(self.actor),
            'xfm_listing_state': '6', 'xfm_trading_open': '0', 'xfm_refund_news_recorded': '1',
            'xfm_news_kind': '10', 'xfm_news_actor': str(self.actor), 'xfm_news_fact_counter': '1', 'xfm_news_last_fact': '1',
            'xfm_actual_raised_cents': '100', 'xfm_external_raised_cents': '0'}
        sub = {'native_id': '80', 'xfm_reservation_id': '8', 'xfm_account': '54', 'xfm_subscription_coin': '70',
            'xfm_subscription_buyer': str(self.actor), 'xfm_subscription_paid_cents': '100',
            'xfm_subscription_units': '500', 'xfm_subscription_state': '3', 'xfm_status': '2', 'xfm_remaining_cents': '0'}
        action = {'query': self.note, 'activation': self.note}
        refund = {'status': 'OBSERVED', 'before_archive': self.base, 'after_archive': self.refunded,
            'gui_actions': {'registration': [action, action], 'subscription': [action], 'abort': [action, action]},
            'facts': {'coin': coin, 'issue_receipt': issue, 'subscription': sub,
                'before': {'free_cents': '1000', 'reserved_cents': '7', 'exchange_fee_cents': '42', 'financial_day': '247'},
                'after': {'free_cents': '900', 'reserved_cents': '7', 'exchange_fee_cents': '142', 'financial_day': '247'}},
            'audit': self.note, 'raw': self.note, 'whole': self.note, 'reconciliation': self.note}
        paid = self.phase(1, physical_archives=[self.base, self.refunded], refund=refund)
        terminal = self.phase(2, physical_archives=[self.base, self.refunded, self.terminal],
            terminal_audit=self.note, terminal_raw=self.note, terminal_whole=self.note,
            toast={'status': 'NOT_OBSERVED', 'reason': 'Authored transport has no Native delivery', 'evidence': [self.note]})
        result = {adapter.ISSUER_REFUND_TOAST_PHASES[i][0]: v for i, v in enumerate((baseline, paid, terminal))}
        for phase in result.values(): phase['evidence'] = [self.source, self.base, self.refunded, self.terminal, self.note]
        return result

    def prepare_and_capture(self):
        adapter.prepare_case(self.context)
        port = CapturePort(self, self.context)
        with patch.object(client_module, 'native_day_request_count', return_value=0):
            row = port.advance_day(allow_event_boundary=True, current_toast_queries=True)
        self.capture = row['current_toast_capture']
        terminal = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[2][0]]
        terminal['day_capture'] = self.capture; terminal['evidence'].append(self.capture)
        return port

    def observed_reports(self):
        capture = adapter.read_json(self.capture['path'])
        scopes = [{'name': n, 'kind': kind, 'observedTag': tag, 'available': True, 'identity': value, 'unavailableReason': ''}
            for n, kind, tag, value in [('xfm_news_recipient', 'CHARACTER', 4, str(self.actor)),
                ('xfm_news_display_entry', 'STORY', 22, '90'), ('xfm_news_actor', 'CHARACTER', 4, str(self.actor))]]
        reports = []
        for i, item in enumerate(capture['queries']):
            toast = {'identity': {'snapshotId': 'native:1', 'nativeRevision': '1', 'publicRevision': '1',
                'gamePid': 999, 'connectionGeneration': '7', 'querySequence': str(i + 1), 'ownerThreadId': 5,
                'completedApplicationFrame': str(100 + i), 'viewerCharacterId': self.actor, 'dateRaw': self.date + 24},
                'stage': 'VISIBLE_PENDING_FRAME' if i == 0 else 'VISIBLE',
                'title': 'Authored software title', 'description': 'Authored software message',
                'guiScopes': scopes, 'scriptScopes': []}
            report = {'schema': 'xfm-news-toast-source-join-candidate-v1', 'machineId': 'software-machine',
                'request': {'schemaVersion': 1, 'machineId': 'software-machine', 'repository': self.context['repo_root'],
                    'toast': item['dto'], 'save': adapter.read_json(self.terminal['path'])['archive'], 'decoder': self.note},
                'producers': {'software_fixture_no_actual_reader_execution': True}, 'newsScriptSources': [self.note],
                'toast': toast, 'assessment': 'UNAVAILABLE' if i == 0 else 'LOCAL_NATIVE_JOIN_MATCH',
                'reason': 'NATIVE_OBJECT_NOT_VISIBLE' if i == 0 else 'NONE',
                'entries': [] if i == 0 else [{'storyId': '90', 'sourceStoryId': '70', 'newsId': '900',
                    'eventId': '1', 'kind': 10, 'day': '247', 'scene': 20, 'actorCharacterId': self.actor}],
                'sources': [] if i == 0 else [{'storyId': '70', 'storyCycle': 'xfm_finance_coin', 'factCounter': '1',
                    'lastFact': '1', 'kind': 10, 'scene': 20, 'actorCharacterId': self.actor}],
                'passes': [] if i == 0 else [{'software_read_fixture': True}] * 3,
                'sourceJoinMatched': i == 1, 'deliveryConfirmed': False, 'allHumanDeliveryConfirmed': False,
                'gameStarted': False, 'financialCertified': False}
            reports.append(self.put('join-' + str(i) + '.json', report))
        final = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[2][0]]
        final['toast'] = {'status': 'OBSERVED', 'joins': reports}; final['evidence'] += reports
        return reports

    def review(self):
        return adapter._irt_review(self.context, {'config': self.context['case_contract']}, self.responses,
            self.date, self.date + 24, self.capture)

    def test_public_prepare_is_passive_only_and_existing17_registry_rows_remain(self):
        with patch.object(adapter, '_saved_fixture_startup', wraps=adapter._saved_fixture_startup) as startup:
            adapter.prepare_case(self.context)
        self.assertIs(True, startup.call_args.kwargs['issuer_refund_toast'])
        self.assertNotIn('case_contract', startup.call_args.args[0])
        profile = Path(self.context['state_dir']) / 'profile/mod-content/fixture'
        text = (profile / 'common/story_cycles/xfma_issuer_refund_toast_passive.txt').read_text(encoding='utf-8-sig')
        self.assertNotIn('effect', text); self.assertNotIn('on_action', text)
        self.assertEqual(26, text.count('visible = no'))
        registry = json.loads((ROOT / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        cases = registry['products']['financial-markets']['cases']
        original_cases, controlled_cases = cases[:-4], cases[-4:]
        self.assertEqual(21, len(original_cases))
        self.assertEqual(['news-delivery-daily', 'perpetual-funding-engine-fixture'],
                         [row['id'] for row in original_cases[-2:]])
        self.assertEqual(['debt-aid-news-engine-fixture', 'synthetic-controlled-load',
                          'crisis-scenes20-engine-fixture', 'futures-risk-engine-fixture'],
                         [row['id'] for row in controlled_cases])
        self.assertEqual(len(cases), len({row['id'] for row in cases}))
        issuer = [row for row in cases if row['id'] == 'issuer-refund-toast']
        self.assertEqual(1, len(issuer))
        self.assertIn('ck3_query_current_interface_toast_v1', issuer[0]['required_mcp_tools'])
        self.assertEqual('coin-campaign-gui', cases[0]['id'])

    def test_ineligible_current_primary_stops_normal_case_without_day_or_queries(self):
        base = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[0][0]]
        base['eligibility'] = {'status': 'NOT_OBSERVED', 'reason': 'Real normal eligibility unavailable', 'evidence': [self.note]}
        adapter.prepare_case(self.context)
        port = RefundRunPort(self, self.context, self.responses, None)
        result = adapter.run_case(self.context, port)
        self.assertEqual('NOT_OBSERVED', result['status']); self.assertFalse(result['case_contract_qualified'])
        self.assertEqual([], port.day_calls); self.assertEqual(1, len(port.requests))

    def test_public_day_composes_exactly_one_original_day_and_two_readonly_rows(self):
        port = self.prepare_and_capture()
        self.assertEqual(1, len(port.calls)); self.assertEqual(3, len(port.calls[0]))
        self.assertEqual('advance_day', port.calls[0][0]['kind']); self.assertEqual(1, port.calls[0][0]['days'])
        self.assertEqual([{}, {}], [r['args'] for r in port.calls[0][1:]])
        self.assertIn(180, port.reserves)
        self.assertTrue(adapter.issuer_refund_toast_plan_matches(self.context, port.calls[0], 'case-natural-day-0001', 300))
        self.assertEqual(2, len(adapter.read_json(self.capture['path'])['queries']))

    def test_native_day_keeps_existing_fresh_before_and_projection_ports(self):
        adapter.prepare_case(self.context); port = CapturePort(self, self.context)
        before = port.full(self.date); before['revision'] = 17
        with patch.object(client_module, 'native_day_request_count', return_value=2), \
                patch.object(client_module, 'latest_frame', return_value=before), \
                patch.object(client_module, 'fresh_native_day_before', return_value=before) as fresh, \
                patch.object(client_module, 'project_native_day', side_effect=lambda row, *a, **k: row) as projection:
            port.advance_day(allow_event_boundary=True, current_toast_queries=True)
        fresh.assert_called_once(); projection.assert_called_once()
        first = port.calls[0][0]
        self.assertEqual('ck3_execute_step', first['tool'])
        self.assertEqual({'step': client_module.NATIVE_DAY_STEP, 'expected_revision': 17}, first['args'])
        self.assertIs(False, first['fresh_revision'])
        self.assertEqual(3, len(port.calls[0]))

    def test_default_public_single_day_is_unchanged_without_optional_flag(self):
        adapter.prepare_case(self.context); port = CapturePort(self, self.context)
        with patch.object(client_module, 'native_day_request_count', return_value=0):
            row = port.advance_day(allow_event_boundary=True)
        self.assertEqual(1, len(port.calls[0])); self.assertNotIn('current_toast_capture', row)
        self.assertEqual([90, 90], port.reserves)

    def test_scope_boolean_day_unknown_extra_or_action_tool_cannot_get_reserved_composition(self):
        self.prepare_and_capture(); original = adapter.read_json(self.capture['path'])
        steps = adapter.read_json(original['plan']['path'])['steps']
        for change in ('days', 'tool', 'extra', 'case'):
            context, altered = copy.deepcopy(self.context), copy.deepcopy(steps)
            if change == 'days': altered[0]['days'] = True
            elif change == 'tool': altered[1]['tool'] = 'ck3_select_event_option'
            elif change == 'extra': altered[1]['args']['force'] = True
            else: context['case'] = 'coin-campaign-gui'; context['case_contract'].pop('issuer_refund_toast_contract')
            with self.subTest(change=change):
                self.assertFalse(adapter.issuer_refund_toast_plan_matches(context, altered, original['name'], 300))

        class GuardReached(Exception): pass
        port = CapturePort(self, self.context)
        with patch.object(port, 'guard', side_effect=GuardReached) as guard:
            with self.assertRaises(GuardReached):
                CaseClient.execute_plan(port, steps, original['name'], 300, reserve=180)
            guard.assert_called_once()
        bad = copy.deepcopy(steps); bad[2]['tool'] = 'ck3_select_event_option'
        with patch.object(port, 'guard') as guard:
            with self.assertRaises(ValueError):
                CaseClient.execute_plan(port, bad, original['name'], 300, reserve=180)
            guard.assert_not_called()

    def test_real_fee_refund_arithmetic_identity_missing_or_zero_paid_is_rejected(self):
        self.prepare_and_capture()
        cell = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[1][0]]['refund']; original = copy.deepcopy(cell)
        for defect in ('fee', 'payer', 'refund', 'remaining', 'missing', 'day', 'external-money'):
            cell.clear(); cell.update(copy.deepcopy(original))
            if defect == 'fee': cell['facts']['issue_receipt']['xfm_issue_receipt_fee_cents'] = '0'
            elif defect == 'payer': cell['facts']['issue_receipt']['xfm_issue_receipt_payer'] = '55'
            elif defect == 'refund': cell['facts']['after']['free_cents'] = '800'
            elif defect == 'remaining': cell['facts']['subscription']['xfm_remaining_cents'] = '100'
            elif defect == 'missing': cell['facts']['issue_receipt'].pop('xfm_issue_receipt_version')
            elif defect == 'day': cell['facts']['after']['financial_day'] = '248'
            else: cell['facts']['issue_receipt']['xfm_issue_receipt_topup_cents'] = '100'
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_absent_native_delivery_stays_NOT_OBSERVED_after_actual_consumer_flow(self):
        self.prepare_and_capture(); result = self.review()
        self.assertTrue(result['issuer_refund_toast']['refund_observed'])
        self.assertFalse(result['issuer_refund_toast']['new_kind10_local_toast_observed'])
        self.assertEqual('NOT_OBSERVED', result['status']); self.assertFalse(result['global_news_delivery_pass'])

    def test_authored_complete_join_exercises_consumer_but_never_grants_global_or_business_credit(self):
        self.prepare_and_capture(); self.observed_reports()
        result = self.review()
        self.assertTrue(result['issuer_refund_toast_case_qualified'])
        for key in ('global_news_delivery_pass', 'all_human_delivery_pass', 'business_pass', 'product_release_pass'):
            self.assertIs(False, result[key])

    def test_older_source_wrong_recipient_or_same_frame_cannot_be_the_new_refund(self):
        self.prepare_and_capture(); reports = self.observed_reports()
        original = adapter.read_json(reports[1]['path'])
        final = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[2][0]]
        for defect in ('old-source', 'actor', 'frame', 'available', 'wrong-save', 'self-credit'):
            value = copy.deepcopy(original)
            if defect == 'old-source': value['entries'][0]['sourceStoryId'] = '69'
            elif defect == 'actor': value['toast']['guiScopes'][0]['identity'] = '9'
            elif defect == 'frame': value['toast']['identity']['completedApplicationFrame'] = '100'
            elif defect == 'available': value['toast']['stage'] = 'EMPTY'
            elif defect == 'wrong-save': value['request']['save'] = adapter.read_json(self.refunded['path'])['archive']
            else: value['deliveryConfirmed'] = True
            changed = self.put('bad-' + defect + '.json', value); final['toast']['joins'][1] = changed
            final['evidence'].append(changed)
            with self.subTest(defect=defect), self.assertRaises(ValueError): self.review()

    def test_full_public_run_uses_existing_Root_protocol_once_and_verify_reconsumes_the_same_pins(self):
        self.prepare_and_capture(); self.observed_reports()
        port = RefundRunPort(self, self.context, self.responses, self.capture)
        result = adapter.run_case(self.context, port)
        self.assertEqual(1, len(port.day_calls)); self.assertEqual(3, len(port.requests))
        self.assertEqual('OBSERVED_LOCAL_SCOPE', result['status'])
        verified = adapter.verify_case(self.context)
        self.assertTrue(verified['issuer_refund_toast_case_qualified'])
        self.assertFalse(verified['business_pass'])

    def test_source_or_case_contract_change_rejected_before_materialization(self):
        for defect in ('day-limit', 'setter-input', 'source'):
            context = copy.deepcopy(self.context)
            if defect == 'day-limit': context['case_contract']['maximum_natural_days'] = True
            elif defect == 'setter-input': context['case_inputs']['AI_gold'] = 100
            else: context['saved_campaign']['sha256'] = 'f' * 64
            with self.subTest(defect=defect), patch('ck3_mod_acceptance_prepare._engine') as engine:
                with self.assertRaises(ValueError): adapter.prepare_case(context)
                engine.assert_not_called()
        self.prepare_and_capture()
        prepared, _ = adapter.compiled_contract(self.context)
        self.assertNotEqual(self.context['case_contract']['post_start'], prepared['config']['post_start'])
        self.assertEqual(self.context['case_inputs']['post_start'], prepared['config']['post_start'])
        canonical = {'config': copy.deepcopy(self.context['case_contract'])}
        canonical_review = adapter._irt_review(self.context, canonical, self.responses,
            self.date, self.date + 24, self.capture)
        prepared_review = adapter._irt_review(self.context, prepared, self.responses,
            self.date, self.date + 24, self.capture)
        self.assertEqual(canonical_review, prepared_review)
        for defect in ('post-predicate', 'contract-field', 'unexpected-field', 'unknown-post-field'):
            changed = copy.deepcopy(prepared)
            if defect == 'post-predicate': changed['config']['post_start']['independent'] = False
            elif defect == 'contract-field': changed['config']['source_contracts'].append('authored-different-source')
            elif defect == 'unexpected-field': changed['config']['unexpected'] = True
            else: changed['config']['post_start']['unknown'] = True
            with self.subTest(compiled_defect=defect), self.assertRaises(ValueError):
                adapter._irt_review(self.context, changed, self.responses,
                    self.date, self.date + 24, self.capture)
        changed_context = copy.deepcopy(self.context)
        changed_context['case_inputs']['post_start']['government_key'] = 'clan_government'
        with self.assertRaises(ValueError):
            adapter._irt_review(changed_context, prepared, self.responses,
                self.date, self.date + 24, self.capture)



    def test_signed32_character_uses_complete_actual_consumer_path_without_unsigned_reinterpretation(self):
        # Authored negative-ID software stimulus, not an observed Game identity.
        self.actor = -2147483648
        self.context['saved_campaign']['player_id'] = self.actor
        self.responses = self.phases()
        self.prepare_and_capture(); self.observed_reports()
        result = self.review()
        self.assertTrue(result['issuer_refund_toast_case_qualified'])
        self.assertFalse(result['global_news_delivery_pass']); self.assertFalse(result['business_pass'])
        baseline = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[0][0]]
        refund = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[1][0]]['refund']['facts']
        self.assertEqual('-2147483648', baseline['eligibility']['PRIMARY']['holder_character_id'])
        for values, field in ((refund['coin'], 'xfm_controller'), (refund['coin'], 'xfm_news_actor'),
                (refund['issue_receipt'], 'xfm_issue_receipt_actor'),
                (refund['subscription'], 'xfm_subscription_buyer')):
            self.assertEqual('-2147483648', values[field])
        port = RefundRunPort(self, self.context, self.responses, self.capture)
        self.assertEqual(self.actor, port.snapshot()['played_character']['character_id'])
        facts = adapter.run_case(self.context, port)
        self.assertTrue(facts['issuer_refund_toast_case_qualified'])
        self.assertTrue(adapter.verify_case(self.context)['issuer_refund_toast_case_qualified'])

    def test_invalid_signed_characters_fail_source_holder_refund_and_named_identity_boundaries(self):
        for value in ('0', '-2147483648', '2147483647', '-2', '31254'):
            self.assertEqual(value, adapter._irt_character(value))
        for value in (-1, -2147483649, 2147483648, True, 1.0):
            context = copy.deepcopy(self.context)
            context['saved_campaign']['player_id'] = value
            with self.subTest(surface='startup', value=value), self.assertRaises(ValueError):
                adapter._irt_inputs(context)
        baseline = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[0][0]]
        refund = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[1][0]]['refund']['facts']
        original_holder = baseline['eligibility']['PRIMARY']['holder_character_id']
        fields = ((refund['coin'], 'xfm_controller'), (refund['coin'], 'xfm_news_actor'),
                  (refund['issue_receipt'], 'xfm_issue_receipt_actor'),
                  (refund['subscription'], 'xfm_subscription_buyer'))
        for bad in ('-1', '-2147483649', '2147483648', '-0', '+1', '01', '-01', False, 1.0):
            baseline['eligibility']['PRIMARY']['holder_character_id'] = bad
            with self.subTest(surface='holder', bad=bad), self.assertRaises(ValueError):
                adapter._irt_baseline(self.context, self.responses, self.date)
            baseline['eligibility']['PRIMARY']['holder_character_id'] = original_holder
            for values, field in fields:
                original = values[field]; values[field] = bad
                with self.subTest(surface=field, bad=bad), self.assertRaises(ValueError):
                    adapter._irt_refund(self.context, self.responses, self.date)
                values[field] = original
            internal = {'guiScopes': [{'name': 'xfm_news_actor', 'kind': 'CHARACTER',
                'observedTag': 4, 'available': True, 'identity': bad, 'unavailableReason': ''}], 'scriptScopes': []}
            public = {'saved_gui_scopes': [{'name': 'xfm_news_actor', 'kind': 'character',
                'observed_tag': 4, 'identity_available': True, 'identity': bad, 'unavailable_reason': None}],
                'saved_script_scopes': []}
            with self.subTest(surface='typed-named', bad=bad), self.assertRaises(ValueError):
                adapter._irt_named(internal, 'xfm_news_actor', 'CHARACTER')
            with self.subTest(surface='public-named', bad=bad), self.assertRaises(ValueError):
                adapter._irt_public_named(public, 'xfm_news_actor', 4)

    def test_signed_character_fix_does_not_expand_story_money_permanent_ids_or_other_cases(self):
        baseline = self.responses[adapter.ISSUER_REFUND_TOAST_PHASES[0][0]]
        account = baseline['eligibility']['PRIMARY']; original = copy.deepcopy(account)
        for field in ('native_id', 'permanent_id', 'free_cents', 'reserved_cents'):
            account.clear(); account.update(original); account[field] = '-2'
            with self.subTest(field=field), self.assertRaises(ValueError):
                adapter._irt_baseline(self.context, self.responses, self.date)
        account.clear(); account.update(original)
        for kind, tag, internal_key, public_key in (('STORY', 22, 'guiScopes', 'saved_gui_scopes'),):
            typed = {internal_key: [{'name': 'xfm_news_display_entry', 'kind': kind, 'observedTag': tag,
                'available': True, 'identity': '-2', 'unavailableReason': ''}], 'scriptScopes': []}
            public = {public_key: [{'name': 'xfm_news_display_entry', 'kind': 'story', 'observed_tag': tag,
                'identity_available': True, 'identity': '-2', 'unavailable_reason': None}], 'saved_script_scopes': []}
            with self.assertRaises(ValueError): adapter._irt_named(typed, 'xfm_news_display_entry', kind)
            with self.assertRaises(ValueError): adapter._irt_public_named(public, 'xfm_news_display_entry', tag)
        other = copy.deepcopy(self.context)
        other['case'] = 'authored-unchanged-other-case'
        other['case_contract']['case_id'] = other['case']
        other['case_contract'].pop('issuer_refund_toast_contract')
        other['saved_campaign']['player_id'] = -2147483648
        with self.assertRaisesRegex(ValueError, 'positive bounded integer player_id'):
            adapter._saved_fixture_startup(other, {})
        thin = {key: copy.deepcopy(other[key]) for key in ('saved_campaign', 'output', 'state_dir')}
        with self.assertRaisesRegex(ValueError, 'positive bounded integer player_id'):
            adapter._saved_fixture_startup(thin, {})
        with self.assertRaisesRegex(ValueError, 'Exact internal issuer refund/toast startup flag'):
            adapter._saved_fixture_startup(thin, {}, issuer_refund_toast=1)


if __name__ == '__main__':
    unittest.main()
