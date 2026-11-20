"""NoGame file/Root/transport ports through actual prepare/day/run/verify code.

Every file, process field, historic record and transport result authored below
is a software input, not a Game observation or newly executed publication.
The real R42 archive DTO is reused by the existing receipt fixture only as a
shape. No production validator or phase/day loop is replaced in these tests.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import json_object, object_field, CONTINUOUS14_PASSIVE_STORY_TYPES_V1
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import ck3_mod_acceptance_prepare as preparation
from test_redemption_gui_case import RedemptionPort, DATE
from test_futures_gui_transactions_case import ACTUAL_R37_ARCHIVE

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / 'tools/ck3_mod_acceptance_cases/financial_markets_redemption_existing_window.json'
HISTORICAL_RUN = '4-8e1c2f1861--financial-markets--R0042'


def note(root: Path, name: str, value: object) -> dict:
    path = root / name
    path.write_text(json.dumps(value), encoding='utf-8')
    return adapter.pin(path)


def software_history(root: Path, context: dict) -> tuple[dict, dict]:
    """Only immutable file-provider inputs; all production cross-links checked."""
    actual = json.loads((REPO / 'tools/ck3_mod_acceptance_cases/financial_markets_redemption_r42_history.json').read_bytes())
    history = copy.deepcopy(actual)
    for name in ('baseline', 'published'):
        source = root / 'historical-profile' / (name + '.ck3')
        source.parent.mkdir(exist_ok=True)
        source.write_bytes(('AUTHORED NO GAME HISTORICAL ' + name).encode())
        saved = root / (name + '.ck3'); saved.write_bytes(source.read_bytes())
        receipt = copy.deepcopy(ACTUAL_R37_ARCHIVE)
        receipt.update(source=adapter.pin(source), archive=adapter.pin(saved), date_raw=DATE)
        receipt['original_checkpoint_result']['checkpoint'].update(path=str(source.resolve()),
            size=source.stat().st_size, sha256=adapter.pin(source)['sha256'], date_raw=DATE)
        history[name + '_archive'] = note(root, name + '-archive.json', receipt)
    history['baseline_pipeline'] = note(root, 'history-baseline-pipeline.json', {'run_id': HISTORICAL_RUN,
        'archive': history['baseline_archive'], 'checkpoint_readback_and_reports_completed': True})
    history['published_pipeline'] = note(root, 'history-published-pipeline.json', {'run_id': HISTORICAL_RUN,
        'archive': history['published_archive'], 'checkpoint_readback_and_reports_completed': True})
    history['reconciliation'] = note(root, 'history-reconciliation.json', {'run_id': HISTORICAL_RUN,
        'window': history['window'], 'baseline_pipeline': history['baseline_pipeline'],
        'published_pipeline': history['published_pipeline'], 'business_pass': False, 'financialCertified': False})
    history['publication_review'] = note(root, 'history-review.json', {'run_id': HISTORICAL_RUN,
        'redemption_publication': {'window': history['window']}})
    history['closure_before_release'] = note(root, 'history-closed.json', {'run_id': HISTORICAL_RUN,
        'normal_close_qualified': True, 'case_acceptance_pass': False, 'public_run_actual_exit_code': 2,
        'public_verify_actual_exit_code': 2, 'new_calendar_days': 0,
        'latest_physical_checkpoint': history['published_archive']})
    history['closure_released'] = note(root, 'history-released.json', {'run_id': HISTORICAL_RUN,
        'closure': history['closure_before_release'], 'actual_resources': [], 'actual_public_closed_lease': True})
    published = json.loads(Path(history['published_archive']['path']).read_bytes())['archive']
    context['saved_campaign'].update(save=published['path'], bytes=published['bytes'],
        sha256=published['sha256'], date_raw=DATE, player_id=31254)
    return history, note(root, 'authored-history-manifest.json', history)


class ExistingWindowPort(RedemptionPort):
    def __init__(self, context: dict, history: dict, manifest: dict) -> None:
        self.context = context; self.history = history; self.manifest = manifest
        self.root = Path(context['output']); self.profile = Path(context['state_dir']) / 'profile'
        self.date = DATE; self.day_calls = 0; self.requests = []
        self.baseline = history['baseline_archive']; self.published = history['published_archive']
        self.terminal = self.archive('one-current-terminal', DATE + 35 * 24)
        self.archives = [self.baseline, self.published, self.terminal]
        self.query = self.note('current-query.json'); self.activation = self.note('current-reclaim-activation.json')
        self.event_context = self.note('current-event-context.json')
        self.event_selection = self.note('current-event-selection.json'); self.event_after = self.note('current-event-after.json')
        self.audit, self.raw, self.whole = (self.note(name) for name in ('terminal-audit.json', 'terminal-raw.json', 'terminal-whole.json'))
        saved = json.loads(Path(self.terminal['path']).read_bytes())['archive']
        ids = ['52', '55', '56', str(history['window']['escrow_native_id']),
            str(history['window']['window_native_id']), '16782900', '67']
        self.selected = note(self.root, 'terminal-explicit-stories.json', {
            'status': 'UNQUALIFIED_EXACT_STORY_DIAGNOSTIC', 'machineId': '4-8e1c2f1861',
            'request': {'save': saved, 'archiveReceipt': self.terminal, 'expectedDateRaw': DATE + 35 * 24,
                'actorIds': ['31254'], 'storyIds': ids}, 'stories': [{'id': item} for item in ids],
            'fullStreamPasses': 1, 'completeStreamBytes': str(saved['bytes']),
            'completeStreamSha256': saved['sha256'], 'inputUnchangedAtGuards': True,
            'before': {'authored_no_game_identity': 'same'}, 'after': {'authored_no_game_identity': 'same'},
            'actorTablePathObserved': True})
        self.metadata, self.differences = (self.note(name) for name in ('source-metadata-comparison.json', 'source-whole-differences.json'))
        log = self.note('authored-operation-log.json')
        wait = note(self.root, 'authored-original-wait.json', {'actual_original_popen_wait': True,
            'returncode': 0, 'stdout': log, 'stderr': log})
        self.pipeline = note(self.root, 'current-terminal-pipeline.json', {
            'schema': 'ck3-continuous14-checkpoint-original-pipeline-v1', 'run_id': context['run_id'],
            'kind': 'terminal', 'archive': self.terminal, 'source_baseline_archive': self.published,
            'actual_date_raw': DATE + 35 * 24, 'prior_date_raw': DATE,
            'checkpoint_readback_and_reports_completed': True,
            'all_original_steps_accepted_with_explicit_exit_policy': True,
            'consumed_completed_SAVE_count': 1, 'reserve_seconds': 180,
            'audit': self.audit, 'actor_raw': self.raw, 'whole_digest': self.whole,
            'metadata_comparison': self.metadata, 'whole_record_comparison': self.differences,
            'original_steps': [{'operation': 'AUDIT-authored-no-Game', 'returncode': 0, 'original_wait': wait}]})
        self.window = copy.deepcopy(history['window'])
        self.cells = {name: {'status': 'NOT_OBSERVED', 'reason': 'Authored port has no actual business evidence',
            'evidence': []} for name in adapter.REDEMPTION_EXISTING_CELLS}
        self.evidence = [manifest, *self.archives, self.query, self.activation, self.event_context,
            self.event_selection, self.event_after, self.audit, self.raw, self.selected, self.whole, self.pipeline, self.metadata, self.differences]

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> dict:
        if allow_actor_change:
            raise AssertionError('No actor change authority')
        return {'date_raw': self.date, 'paused': True, 'active_event': None, 'pending_character_interaction': None,
            'source': 'injected-dll-named-pipe', 'played_character': {'character_id': 31254, 'alive': True, 'source': 'native'},
            'managed_campaign_run_binding': {'run_id': self.context['run_id'], 'state_dir': self.context['state_dir']}}

    def root_checkpoint(self, name: str, request: dict, reserve: int = 90) -> dict:
        if reserve != 90:
            raise AssertionError('Original Root reserve changed')
        self.requests.append(name)
        response = {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {key: True for key in request['required_assertions']}, 'evidence': list(self.evidence)}
        if name == adapter.REDEMPTION_EXISTING_PHASES[0]:
            current = note(self.root, 'current-cold-snapshot.json', self.snapshot())
            response['evidence'].append(current)
            response.update(source_history_manifest=self.manifest, current_snapshot=current,
                window_queries=[self.query], window=self.window)
        elif name == adapter.REDEMPTION_EXISTING_PHASES[1]:
            response.update(physical_archives=self.archives, terminal_pipeline=self.pipeline,
                terminal_audit=self.audit, terminal_raw=self.raw, terminal_selected_raw=self.selected, terminal_whole_graph=self.whole,
                redemption_existing_cells=self.cells)
        else:
            raise AssertionError('No republish or legacy GUI phase is permitted')
        return response

    def observe_ai(self) -> dict:
        cell = self.observed('independent_ai_redemption')
        cell['raw'] = self.selected
        cell.update(before_archive=self.published, after_archive=self.terminal, receipt={
            'native_id': 16782900, 'id': 1, 'coin_native_id': 55, 'coin_id': 1,
            'window_native_id': self.window['window_native_id'], 'window_id': 1,
            'payer_native_id': self.window['escrow_native_id'], 'payer_id': self.window['escrow_id'],
            'payee_native_id': 67, 'payee_id': 8, 'holder_id': 34973, 'beneficiary_id': 34973,
            'controller_id': 31254, 'paid_units': 100, 'paid_cents': 21, 'price_cents': 21,
            'financial_day': 122, 'status': 1, 'identity_version': 1, 'is_ai': 1,
            'primary_known': 1, 'primary_native_id': 67, 'primary_id': 8, 'used_primary': 1})
        self.cells['independent_ai_redemption'] = cell; return cell

    def observe_reclaim(self) -> dict:
        cell = self.observed('expired_remainder_return')
        cell['raw'] = self.selected
        cell.update(before_archive=self.published, after_archive=self.terminal,
            gui_actions=self.actions(), confirmation=self.confirmation(), reclaim={
            'window_native_id': self.window['window_native_id'], 'window_id': 1, 'financial_day': 156,
            'remaining_before_cents': 979, 'reclaimed_delta_cents': 979, 'remaining_after_cents': 0,
            'escrow_before_cents': 979, 'escrow_after_cents': 0,
            'issuer_free_before_cents': 500, 'issuer_free_after_cents': 1479,
            'issuer_reserved_before_cents': 140, 'issuer_reserved_after_cents': 140,
            'reclaimed_before_cents': 0, 'reclaimed_after_cents': 979, 'status': 4,
            'receipt_version': 1, 'actor_id': 31254, 'coin_native_id': 55, 'coin_id': 1,
            'issuer_native_id': 56, 'issuer_id': 3, 'escrow_native_id': self.window['escrow_native_id'],
            'escrow_id': self.window['escrow_id'], 'initial_cents': 1000, 'paid_before_cents': 21,
            'paid_after_cents': 21, 'status_before': 1, 'escrow_reserved_before_cents': 0,
            'escrow_reserved_after_cents': 0})
        self.cells['expired_remainder_return'] = cell; return cell


class RedemptionExistingWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        from test_continuous14_clock_diagnostic import Continuous14PrepareJsonBoundaryTests
        temporary = tempfile.TemporaryDirectory(prefix='existing-window-software-'); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        context = Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.history, self.manifest = software_history(self.root, context)
        config = json.loads(CONFIG.read_bytes()); config['source_history_manifest'] = self.manifest
        self.constant = patch.object(adapter, 'REDEMPTION_EXISTING_HISTORY', self.manifest)
        self.constant.start(); self.addCleanup(self.constant.stop)
        context.update(product='financial-markets', case='redemption-existing-window', case_contract=config,
            run_id='authored-current-existing-window', case_spec={'budgets': {'command_timeout': 300}})
        self.context = context
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            self.prepared = adapter.prepare_case(context)
        self.assertGreaterEqual(engine.call_count, 1)
        self.port = ExistingWindowPort(context, self.history, self.manifest)

    def run_case(self) -> dict:
        return adapter.run_case(self.context, self.port)

    def test_actual_prepare_engine_json_35_day_loop_and_verify_have_only_two_new_phases(self) -> None:
        self.assertEqual(json.loads(json.dumps(self.prepared)), self.prepared)
        facts = self.run_case()
        self.assertEqual(self.port.requests, list(adapter.REDEMPTION_EXISTING_PHASES))
        self.assertEqual(self.port.day_calls, 35)
        self.assertEqual(facts['current_physical_checkpoint_count'], 1)
        self.assertEqual(facts['retained_physical_checkpoint_count'], 3)
        self.assertEqual(facts['observed_cells'], [])
        self.assertEqual(adapter.verify_case(self.context)['not_observed_cells'], list(adapter.REDEMPTION_EXISTING_CELLS))
        for key in ('current_publication_credit', 'cold_same_day_complete_graph_credit', 'financial_clock_qualified',
                    'historical_publication_phase_consumed', 'historical_case_acceptance_pass',
                    'business_pass', 'product_release_pass', 'financialCertified'):
            self.assertIs(facts[key], False)
        self.assertNotIn('normal_close_qualified', facts)

    def test_passive_catalog_initial_plan_and_existing_registry_budgets_stay_finite(self) -> None:
        passive = Path(self.prepared['profile_preparation']['profile']) / 'mod-content/fixture/common/story_cycles/xfma_redemption_existing_passive.txt'
        self.assertEqual(passive.read_text(encoding='utf-8-sig'), ''.join(name + ' = { visible = no }\n' for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
        self.assertEqual(json.loads((Path(self.context['output']) / 'initial-plan.json').read_bytes()), {'steps': []})
        registry = json.loads((REPO / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        cases = registry['products']['financial-markets']['cases']
        selected = next(row for row in cases if row['id'] == 'redemption-existing-window')
        original = next(row for row in cases if row['id'] == 'redemption-gui')
        self.assertEqual(selected['budgets'], original['budgets'])
        self.assertEqual(selected['normal_close'], original['normal_close'])
        self.assertEqual(selected['normal_close']['reserve_seconds'], 180)

    def test_wrong_or_alias_history_manifest_is_rejected_before_any_day(self) -> None:
        alias = note(self.root, 'history-alias.json', self.history)
        self.port.manifest = alias; self.port.evidence.append(alias)
        with self.assertRaisesRegex(ValueError, 'exact paid source history'):
            self.run_case()
        self.assertEqual(self.port.day_calls, 0)

    def test_foreign_history_cannot_be_relabelled_current_or_turn_old_GAP_into_pass(self) -> None:
        context = copy.deepcopy(self.context); context['run_id'] = HISTORICAL_RUN
        with self.assertRaisesRegex(ValueError, 'historical and unconsumed'):
            adapter._redemption_existing_history(json_object(context))
        changed = copy.deepcopy(self.history); changed['publication_phase_consumed'] = True
        ref = note(self.root, 'false-history-pass.json', changed)
        context['case_contract']['source_history_manifest'] = ref
        with patch.object(adapter, 'REDEMPTION_EXISTING_HISTORY', ref):
            with self.assertRaisesRegex(ValueError, 'historical and unconsumed'):
                adapter._redemption_existing_history(json_object(context))

    def test_wrong_forward_source_is_refused_before_private_engine_or_Game(self) -> None:
        context = copy.deepcopy(self.context); context['saved_campaign']['sha256'] = 'a' * 64
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            with self.assertRaisesRegex(ValueError, 'paid forward source'):
                adapter.prepare_case(context)
        self.assertEqual(engine.call_count, 0)

    def test_current_cold_snapshot_actor_run_date_and_window_are_not_historical_defaults(self) -> None:
        compiled, _ = adapter.compiled_contract(self.context)
        spec = compiled['config']['gui_phases'][0]
        phase = self.port.root_checkpoint(spec['id'], {'required_assertions': spec['requirements']})
        for field, value in (('date_raw', DATE + 24), ('paused', False), ('source', 'authored-other-source')):
            with self.subTest(field=field):
                current = copy.deepcopy(phase); snapshot = self.port.snapshot(); snapshot[field] = value
                ref = note(self.root, field + '-bad-snapshot.json', snapshot)
                current['current_snapshot'] = ref; current['evidence'].append(ref)
                with self.assertRaisesRegex(ValueError, 'New cold Native'):
                    adapter._redemption_existing_binding(json_object(self.context), json_object(current), DATE)
        wrong = copy.deepcopy(phase); wrong['window']['window_id'] = True
        with self.assertRaisesRegex(ValueError, 'Exact bounded redemption integer'):
            adapter._redemption_existing_binding(json_object(self.context), json_object(wrong), DATE)

    def test_unknown_AI_and_missing_financial_expiry_remain_NOT_OBSERVED(self) -> None:
        facts = self.run_case()
        self.assertEqual(facts['not_observed_cells'], list(adapter.REDEMPTION_EXISTING_CELLS))
        self.assertIs(facts['business_pass'], False)

    def test_positive_current_reclaim_and_independent_receipt_have_local_credit_only(self) -> None:
        self.port.observe_ai(); self.port.observe_reclaim()
        facts = self.run_case()
        self.assertEqual(facts['observed_cells'], list(adapter.REDEMPTION_EXISTING_CELLS))
        self.assertEqual(adapter.verify_case(self.context)['observed_cells'], facts['observed_cells'])
        self.assertIs(facts['current_publication_credit'], False)

    def test_calendar_only_expiry_zero_remainder_or_cash_created_cannot_gain_return_credit(self) -> None:
        cell = self.port.observe_reclaim(); original = copy.deepcopy(cell['reclaim'])
        for key, value in (('financial_day', 150), ('remaining_before_cents', 0), ('issuer_free_after_cents', 1480),
                           ('issuer_reserved_after_cents', 139), ('reclaimed_after_cents', 1958), ('status', 1)):
            with self.subTest(key=key):
                cell['reclaim'] = {**original, key: value}
                with self.assertRaisesRegex(ValueError, 'once-only escrow-to-issuer'):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_self_redemption_wrong_window_or_expired_AI_receipt_does_not_gain_credit(self) -> None:
        cell = self.port.observe_ai(); original = copy.deepcopy(cell['receipt'])
        for key, value in (('holder_id', 31254), ('window_id', 2), ('paid_cents', 20), ('financial_day', 151)):
            with self.subTest(key=key):
                cell['receipt'] = {**original, key: value}
                with self.assertRaisesRegex(ValueError, 'independently owned'):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_new_D0_save_fourth_archive_or_receipt_alias_cannot_multiply_endpoints(self) -> None:
        original = list(self.port.archives)
        for receipts in ([*original, original[2]], [original[0], original[1], original[1]], [original[2], original[1], original[2]]):
            with self.subTest(receipts=receipts):
                self.port.archives = receipts
                with self.assertRaises(ValueError):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_non_player_holder_without_actual_AI_identity_snapshot_has_no_AI_credit(self) -> None:
        cell = self.port.observe_ai(); original = copy.deepcopy(cell['receipt'])
        for key in ('identity_version', 'is_ai', 'primary_known', 'used_primary'):
            for value in (0, True, '1', None):
                with self.subTest(key=key, value=value):
                    cell['receipt'] = {**original, key: value}
                    with self.assertRaises(ValueError):
                        self.run_case()
                    self.port.date = DATE; self.port.day_calls = 0
        cell['receipt'] = {key: value for key, value in original.items() if key != 'identity_version'}
        with self.assertRaisesRegex(ValueError, 'immutable natural AI receipt'):
            self.run_case()

    def test_actual_AI_PRIMARY_snapshot_must_match_the_real_receipt_payee(self) -> None:
        cell = self.port.observe_ai(); original = copy.deepcopy(cell['receipt'])
        for key, value in (('primary_native_id', 68), ('primary_id', 9), ('identity_version', 2)):
            with self.subTest(key=key):
                cell['receipt'] = {**original, key: value}
                with self.assertRaisesRegex(ValueError, 'independently owned'):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_return_requires_the_actual_success_version_and_same_coin_window_accounts(self) -> None:
        cell = self.port.observe_reclaim(); original = copy.deepcopy(cell['reclaim'])
        for key, value in (('receipt_version', 0), ('receipt_version', True), ('actor_id', 31255),
                           ('coin_native_id', 57), ('coin_id', 2), ('issuer_native_id', 58),
                           ('issuer_id', 4), ('escrow_native_id', 16782756), ('escrow_id', 4873)):
            with self.subTest(key=key, value=value):
                cell['reclaim'] = {**original, key: value}
                with self.assertRaises(ValueError):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0
        cell['reclaim'] = {key: value for key, value in original.items() if key != 'receipt_version'}
        with self.assertRaisesRegex(ValueError, 'isolated current pre/post'):
            self.run_case()

    def test_return_receipt_cannot_change_paid_total_or_reclaim_old_cash_twice(self) -> None:
        cell = self.port.observe_reclaim(); original = copy.deepcopy(cell['reclaim'])
        for key, value in (('initial_cents', 1001), ('paid_before_cents', 20), ('paid_after_cents', 22),
                           ('reclaimed_before_cents', 1), ('status_before', 4),
                           ('escrow_reserved_before_cents', 1), ('escrow_reserved_after_cents', 1)):
            with self.subTest(key=key):
                cell['reclaim'] = {**original, key: value}
                with self.assertRaisesRegex(ValueError, 'once-only escrow-to-issuer'):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_contract_cannot_add_publication_observer_days_or_larger_SAVE(self) -> None:
        for key, value in (('maximum_natural_days', 36), ('allow_actor_change', True), ('fixture_emitter', {})):
            with self.subTest(key=key):
                config = copy.deepcopy(self.context['case_contract']); config[key] = value
                with self.assertRaisesRegex(ValueError, 'Exact source-bound'):
                    adapter._redemption_existing_enabled(json_object({**self.context, 'case_contract': config}))
        for key, value in (('physical_save_max_bytes', 385 * 1024 * 1024), ('republish', True), ('observer_arm', True)):
            with self.subTest(key=key):
                config = copy.deepcopy(self.context['case_contract']); config['redemption_existing_window_contract'][key] = value
                with self.assertRaisesRegex(ValueError, 'Exact source-bound'):
                    adapter._redemption_existing_enabled(json_object({**self.context, 'case_contract': config}))

    def test_verify_rechecks_history_pipeline_and_current_local_credit(self) -> None:
        self.run_case(); path = Path(self.context['output']) / 'generic-product-case-result.json'
        facts = json.loads(path.read_bytes()); facts['current_publication_credit'] = True
        path.write_text(json.dumps(facts), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'local credit changed'):
            adapter.verify_case(self.context)


if __name__ == '__main__':
    unittest.main()
