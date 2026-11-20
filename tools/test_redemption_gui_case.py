"""NoGame tests of the real generic prepare/phase/day/review/verify producers.

All SAVE bytes, Root reviews and transport frames below are labelled authored
software inputs. The retained real R37 receipt supplies the public DTO shape;
its Native false physical flag is never converted to a live SAVE claim.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from ck3_mod_acceptance_background_types import (
    CONTINUOUS14_PASSIVE_STORY_TYPES_V1, JsonObject, json_object, object_field,
)
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import ck3_mod_acceptance_prepare as preparation
import test_futures_gui_transactions_case as original_receipt

DATE = 53147328
CONFIG = REPO / 'tools/ck3_mod_acceptance_cases/financial_markets_redemption_gui.json'


class RedemptionPort:
    """Only file/Root/transport ports, with no copied production phase loop."""

    def __init__(self, context: JsonObject) -> None:
        self.context = context
        self.root = Path(str(context['output']))
        self.profile = Path(str(context['state_dir'])) / 'profile'
        self.date = DATE
        self.day_calls = 0
        self.requests: list[str] = []
        self.baseline = self.archive('cold-baseline', DATE)
        self.published = self.archive('published', DATE)
        self.terminal = self.archive('terminal', DATE + 35 * 24)
        self.query = self.note('normal-query.json')
        self.activation = self.note('normal-activation.json')
        self.event_context = self.note('actual-event-context.json')
        self.event_selection = self.note('actual-event-selection.json')
        self.event_after = self.note('actual-event-after.json')
        self.audit, self.raw, self.whole = (self.note(name) for name in ('audit.json', 'raw.json', 'whole.json'))
        startup = object_field(context, 'saved_campaign')
        source = copy.deepcopy(original_receipt.ACTUAL_R37_ARCHIVE)
        source.update(date_raw=DATE, archive={'path': startup['save'], 'bytes': startup['bytes'], 'sha256': startup['sha256']})
        path = self.root / 'prior-source.archive.json'
        path.write_text(json.dumps(source), encoding='utf-8')
        self.source = adapter.pin(path)
        self.evidence = [self.baseline, self.published, self.terminal, self.source, self.query, self.activation,
            self.event_context, self.event_selection, self.event_after, self.audit, self.raw, self.whole]
        self.archives = [self.baseline, self.published, self.terminal]
        self.window: JsonObject = {
            'coin_native_id': 55, 'coin_id': 1, 'window_native_id': 9200, 'window_id': 1,
            'issuer_native_id': 56, 'issuer_id': 3, 'escrow_native_id': 9201, 'escrow_id': 990,
            'publisher_id': 31254, 'controller_id': 31254, 'price_cents': 20,
            'initial_budget_cents': 1000, 'remaining_cents': 1000, 'paid_cents': 0,
            'paid_units': 0, 'reclaimed_cents': 0, 'created_financial_day': 121,
            'expiry_financial_day': 151, 'duration_days': 30, 'status': 1,
        }
        self.publication = self.observed('prefunded_publish')
        self.publication.update(before_archive=self.baseline, after_archive=self.published,
            gui_actions=self.actions(), confirmation=self.confirmation(), window=self.window)
        self.cells: JsonObject = {'prefunded_publish': self.publication,
            **{name: {'status': 'NOT_OBSERVED', 'reason': 'Authored transport has no real AI or return observation', 'evidence': []}
               for name in adapter.REDEMPTION_GUI_CELLS[1:]}}

    def note(self, name: str) -> JsonObject:
        path = self.root / name
        path.write_text(json.dumps({'authored_no_game_input': name}), encoding='utf-8')
        return adapter.pin(path)

    def archive(self, name: str, date: int) -> JsonObject:
        source = self.profile / 'save games' / (name + '.ck3')
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('AUTHORED SOFTWARE INPUT ONLY ' + name, encoding='utf-8')
        saved = self.root / (name + '.ck3')
        saved.write_bytes(source.read_bytes())
        source_pin = adapter.pin(source)
        receipt = copy.deepcopy(original_receipt.ACTUAL_R37_ARCHIVE)
        receipt.update(source=source_pin, archive=adapter.pin(saved), date_raw=date)
        receipt['original_checkpoint_result']['checkpoint'].update(path=source_pin['path'],
            size=source_pin['bytes'], sha256=source_pin['sha256'], date_raw=date)
        path = self.root / (name + '.archive.json')
        path.write_text(json.dumps(receipt), encoding='utf-8')
        return adapter.pin(path)

    def observed(self, name: str) -> JsonObject:
        assertions = {key: True for key in adapter.REDEMPTION_GUI_COMMON_ASSERTIONS}
        assertions[adapter.REDEMPTION_GUI_CELL_ASSERTIONS[name]] = True
        return {'status': 'OBSERVED', 'assertions': assertions, 'audit': self.audit, 'raw': self.raw, 'whole_graph': self.whole}

    def actions(self) -> list[JsonObject]:
        return [{'query': self.query, 'activation': self.activation}]

    def confirmation(self) -> JsonObject:
        return {'context': self.event_context, 'selection': self.event_selection, 'after_snapshot': self.event_after}

    def observe_ai(self) -> JsonObject:
        cell = self.observed('independent_ai_redemption')
        cell.update(before_archive=self.published, after_archive=self.terminal, receipt={
            'native_id': 9300, 'id': 1, 'coin_native_id': 55, 'coin_id': 1,
            'window_native_id': 9200, 'window_id': 1, 'payer_native_id': 9201, 'payer_id': 990,
            'payee_native_id': 67, 'payee_id': 8, 'holder_id': 34973, 'beneficiary_id': 34973,
            'controller_id': 31254, 'paid_units': 100, 'paid_cents': 20, 'price_cents': 20,
            'financial_day': 122, 'status': 1})
        self.cells['independent_ai_redemption'] = cell
        return cell

    def observe_reclaim(self, *, remaining: int = 1000) -> JsonObject:
        cell = self.observed('expired_remainder_return')
        cell.update(before_archive=self.published, after_archive=self.terminal, gui_actions=self.actions(),
            confirmation=self.confirmation(), reclaim={'window_native_id': 9200, 'window_id': 1,
                'financial_day': 156, 'remaining_before_cents': remaining, 'reclaimed_delta_cents': remaining,
                'remaining_after_cents': 0, 'escrow_after_cents': 0, 'status': 4})
        self.cells['expired_remainder_return'] = cell
        return cell

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> JsonObject:
        if allow_actor_change:
            raise AssertionError('No actor transition authority')
        return {'date_raw': self.date, 'paused': True, 'active_event': None, 'pending_character_interaction': None}

    def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90) -> JsonObject:
        if reserve != 90:
            raise AssertionError('Existing Root phase reserve changed')
        self.requests.append(name)
        requirements = request['required_assertions']
        if not isinstance(requirements, list):
            raise AssertionError('Actual production Root request required')
        result: JsonObject = {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {str(key): True for key in requirements}, 'evidence': self.evidence}
        if name == adapter.REDEMPTION_GUI_PHASES[0]:
            result.update(source_archive=self.source, baseline_archive=self.baseline,
                baseline_audit=self.audit, baseline_raw=self.raw, baseline_whole_graph=self.whole)
        elif name == adapter.REDEMPTION_GUI_PHASES[1]:
            result['redemption_publication'] = self.publication
        elif name == adapter.REDEMPTION_GUI_PHASES[2]:
            result.update(redemption_gui_cells=self.cells, physical_archives=self.archives,
                terminal_audit=self.audit, terminal_raw=self.raw, terminal_whole_graph=self.whole)
        else:
            raise AssertionError('No automatic event resolution or hidden business step')
        return result

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False,
                    allow_actor_change: bool = False, pending_interaction_policy: str = 'stop_at_boundary') -> dict[str, object]:
        if days != 1 or not allow_event_boundary or allow_actor_change or pending_interaction_policy != 'stop_at_boundary':
            raise AssertionError('Only the unchanged bounded public one-day path is permitted')
        before = self.snapshot()
        self.date += 24
        self.day_calls += 1
        return {'result': {'requested_days': 1, 'requested_interval_complete': True,
            'before': before, 'after': self.snapshot()}}

    def execute_plan(self, *args: object, **kwargs: object) -> list[dict[str, object]]:
        raise AssertionError('No hidden setter, forced business or separate executor')

    def checkpoint(self, name: str, value: JsonObject) -> Path:
        path = self.root / (name + '.json')
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def log_bytes(self) -> bytes:
        return b''  # No fake marker/ARM/PASS lines.


class RedemptionGuiCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        from test_continuous14_clock_diagnostic import Continuous14PrepareJsonBoundaryTests
        temporary = tempfile.TemporaryDirectory(prefix='redemption-gui-software-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = json_object(json.loads(CONFIG.read_bytes()))
        context = Continuous14PrepareJsonBoundaryTests().context(self.root)
        context.update(product='financial-markets', case='redemption-gui', case_contract=copy.deepcopy(self.config),
            run_id='authored-redemption-only', case_spec={'budgets': {'command_timeout': 300}})
        object_field(json_object(context), 'saved_campaign')  # Actual public shape validation.
        context['saved_campaign']['date_raw'] = DATE
        self.context = context
        self.source_contract = copy.deepcopy(context['case_contract'])
        with patch.object(preparation, '_engine', wraps=preparation._engine) as engine:
            self.prepared = adapter.prepare_case(context)
        self.assertGreaterEqual(engine.call_count, 1)
        self.port = RedemptionPort(json_object(context))

    def run_case(self) -> JsonObject:
        return json_object(adapter.run_case(self.context, self.port))

    def test_real_saved_prepare_json_run_verify_and_original_bounded_day_loop(self) -> None:
        self.assertEqual(json.loads(json.dumps(self.prepared)), self.prepared)
        compiled, _ = adapter.compiled_contract(self.context)
        self.assertEqual(compiled['config']['post_start'], self.context['case_inputs']['post_start'])
        self.assertEqual(self.context['case_contract'], self.source_contract)
        self.assertTrue(all(value is None for value in self.source_contract['post_start'].values()))
        facts = self.run_case()
        self.assertEqual(self.port.requests, list(adapter.REDEMPTION_GUI_PHASES))
        self.assertEqual(self.port.day_calls, 35)
        self.assertEqual(facts['observed_cells'], ['prefunded_publish'])
        self.assertEqual(facts['not_observed_cells'], ['independent_ai_redemption', 'expired_remainder_return'])
        self.assertEqual(adapter.verify_case(self.context)['observed_cells'], facts['observed_cells'])
        for key in ('business_pass', 'product_release_pass', 'financial_clock_qualified', 'toast_delivery_qualified'):
            self.assertIs(facts[key], False)
        self.assertNotIn('normal_close_qualified', facts)

    def test_passive_catalog_has_only_original_finite_declarations_and_no_observer_arm(self) -> None:
        profile = Path(self.prepared['profile_preparation']['profile'])
        passive = profile / 'mod-content/fixture/common/story_cycles/xfma_redemption_gui_passive.txt'
        text = passive.read_text(encoding='utf-8-sig')
        self.assertEqual(text, ''.join(name + ' = { visible = no }\n' for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
        for forbidden in ('effect', 'on_action', 'on_start', 'log', 'timer', 'xfma_armed', 'set_variable'):
            self.assertNotIn(forbidden, text)
        self.assertEqual(json.loads((Path(self.context['output']) / 'initial-plan.json').read_bytes()), {'steps': []})

    def test_no_ai_or_empty_or_not_yet_expired_return_remains_explicitly_unobserved(self) -> None:
        self.port.cells['expired_remainder_return'] = {'status': 'NOT_OBSERVED',
            'reason': 'Actual finance day still below expiry; calendar35 is not proof', 'evidence': [self.port.raw]}
        facts = self.run_case()
        self.assertEqual(facts['not_observed_cells'], list(adapter.REDEMPTION_GUI_CELLS[1:]))
        self.assertIs(facts['case_contract_qualified'], True)
        self.assertFalse(facts['business_pass'])

    def test_independent_receipt_and_real_positive_expired_remainder_have_only_local_credit(self) -> None:
        self.port.observe_ai()
        self.port.observe_reclaim(remaining=980)
        facts = self.run_case()
        self.assertEqual(facts['observed_cells'], list(adapter.REDEMPTION_GUI_CELLS))
        self.assertEqual(facts['not_observed_cells'], [])
        self.assertIs(adapter.verify_case(self.context)['business_pass'], False)
        self.assertEqual(facts['retained_physical_checkpoint_count'], 3)

    def test_failed_publication_is_rejected_before_any_natural_day_dispatch(self) -> None:
        self.port.publication = {'status': 'NOT_OBSERVED', 'reason': 'Real normal GUI publication unavailable', 'evidence': []}
        with self.assertRaisesRegex(ValueError, 'Publication must actually succeed'):
            self.run_case()
        self.assertEqual(self.port.day_calls, 0)
        self.assertFalse((self.port.root / 'generic-product-case-result.json').exists())

    def test_bad_source_binding_fails_before_publish_phase_or_draft_initialization(self) -> None:
        source = Path(str(self.port.source['path']))
        data = json.loads(source.read_bytes()); data['archive']['sha256'] = 'a' * 64
        source.write_text(json.dumps(data), encoding='utf-8')
        old = self.port.source
        self.port.source = adapter.pin(source)
        self.port.evidence[self.port.evidence.index(old)] = self.port.source
        with self.assertRaisesRegex(ValueError, 'prior source archive'):
            self.run_case()
        self.assertEqual(self.port.requests, [adapter.REDEMPTION_GUI_PHASES[0]])
        self.assertEqual(self.port.day_calls, 0)

    def test_wrong_budget_window_price_duration_coin_or_missing_field_cannot_publish(self) -> None:
        original = copy.deepcopy(self.port.window)
        for field, value in (('coin_native_id', 63), ('initial_budget_cents', 1001), ('remaining_cents', 999),
                             ('price_cents', 0), ('duration_days', 90), ('escrow_native_id', 56),
                             ('publisher_id', True), ('paid_cents', 1)):
            with self.subTest(field=field):
                self.port.window.clear(); self.port.window.update(original); self.port.window[field] = value
                with self.assertRaises(ValueError):
                    self.run_case()
                self.assertEqual(self.port.day_calls, 0)
        self.port.window.clear(); self.port.window.update(original); self.port.window.pop('paid_units')
        with self.assertRaisesRegex(ValueError, 'missing fields'):
            self.run_case()

    def test_player_self_receipt_wrong_window_price_or_expired_receipt_cannot_gain_ai_credit(self) -> None:
        cell = self.port.observe_ai()
        original = copy.deepcopy(object_field(cell, 'receipt'))
        for field, value in (('holder_id', 31254), ('beneficiary_id', 31254), ('window_id', 2),
                             ('paid_cents', 21), ('paid_units', 200), ('financial_day', 151), ('payer_id', 3)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(original); receipt[field] = value; cell['receipt'] = receipt
                with self.assertRaises(ValueError):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_calendar_expiry_zero_balance_or_duplicate_return_does_not_prove_fund_return(self) -> None:
        cell = self.port.observe_reclaim()
        original = copy.deepcopy(object_field(cell, 'reclaim'))
        for field, value in (('financial_day', 150), ('remaining_before_cents', 0),
                             ('reclaimed_delta_cents', 0), ('escrow_after_cents', 1), ('status', 1)):
            with self.subTest(field=field):
                value_object = copy.deepcopy(original); value_object[field] = value; cell['reclaim'] = value_object
                with self.assertRaises(ValueError):
                    self.run_case()
                self.port.date = DATE; self.port.day_calls = 0

    def test_publication_and_reclaim_need_actual_confirmation_and_per_activation_query(self) -> None:
        self.port.publication['confirmation'] = {'selection': self.port.event_selection}
        with self.assertRaisesRegex(ValueError, 'event context'):
            self.run_case()
        self.assertEqual(self.port.day_calls, 0)
        self.port.publication['confirmation'] = self.port.confirmation()
        self.port.publication['gui_actions'] = [{'activation': self.port.activation}]
        with self.assertRaisesRegex(ValueError, 'fresh query'):
            self.run_case()

    def test_false_independent_accounting_assertion_never_converts_to_local_credit(self) -> None:
        assertions = object_field(self.port.publication, 'assertions')
        assertions[adapter.REDEMPTION_GUI_COMMON_ASSERTIONS[-1]] = False
        self.port.publication['assertions'] = assertions
        with self.assertRaisesRegex(ValueError, 'individually reconciled'):
            self.run_case()

    def test_archive_receipt_alias_same_physical_save_or_fourth_checkpoint_is_rejected(self) -> None:
        alias = self.port.root / 'same-published-second-receipt.json'
        alias.write_bytes(Path(str(self.port.published['path'])).read_bytes())
        reference = adapter.pin(alias); self.port.evidence.append(reference)
        self.port.archives[2] = reference
        with self.assertRaises(ValueError):
            self.run_case()
        self.port.date = DATE; self.port.day_calls = 0
        self.port.archives = [self.port.baseline, self.port.published, self.port.terminal, reference]
        with self.assertRaisesRegex(ValueError, 'Exactly three'):
            self.run_case()

    def test_real_native_false_flag_is_kept_and_saved_materialization_failures_are_rejected(self) -> None:
        reference = self.port.baseline
        original = json.loads(Path(str(reference['path'])).read_bytes())
        self.assertIs(original['original_checkpoint_result']['physical_save_confirmed'], False)
        for change in ('native-true', 'not-saved', 'not-materialized', 'wrong-date', 'cross-run-source'):
            with self.subTest(change=change):
                data = copy.deepcopy(original)
                native = data['original_checkpoint_result']
                if change == 'native-true': native['physical_save_confirmed'] = True
                elif change == 'not-saved': native['checkpoint']['status'] = 'submitted'
                elif change == 'not-materialized': native['materialization']['available'] = False
                elif change == 'wrong-date': data['date_raw'] += 24
                else:
                    data['source']['path'] = str(self.root / 'other-run' / 'xar.ck3')
                    native['checkpoint']['path'] = data['source']['path']
                path = self.port.root / (change + '.archive.json'); path.write_text(json.dumps(data), encoding='utf-8')
                current = adapter.pin(path)
                with self.assertRaises(ValueError):
                    adapter._redemption_gui_archive(current, {'evidence': [current]}, DATE, json_object(self.context))

    def test_exact_contract_refuses_other_case_or_scope_or_calendar_widening(self) -> None:
        for field, value in (('maximum_natural_days', True), ('maximum_natural_days', 36),
                             ('allow_actor_change', True), ('fixture_emitter', {}),
                             ('passive_story_types', [*CONTINUOUS14_PASSIVE_STORY_TYPES_V1, 'xfma_unknown'])):
            with self.subTest(field=field):
                config = copy.deepcopy(self.config); config[field] = value
                with self.assertRaises(ValueError):
                    adapter._redemption_gui_enabled(json_object({**self.context, 'case_contract': config}))
        with self.assertRaises(ValueError):
            adapter._redemption_gui_enabled(json_object({**self.context, 'case': 'lifecycle'}))

    def test_nonnull_original_post_start_cannot_be_overwritten_in_run_or_verify(self) -> None:
        self.run_case()
        self.context['case_contract']['post_start']['government_key'] = 'feudal_government'
        self.context['case_inputs']['post_start']['government_key'] = 'clan_government'
        with self.assertRaisesRegex(ValueError, 'Cannot overwrite'):
            adapter.run_case(self.context, self.port)
        with self.assertRaisesRegex(ValueError, 'Cannot overwrite'):
            adapter.verify_case(self.context)

    def test_verify_rechecks_original_credit_and_evidence_instead_of_trusting_result_flags(self) -> None:
        self.run_case()
        path = self.port.root / 'generic-product-case-result.json'
        facts = json.loads(path.read_bytes()); facts['observed_cells'].append('independent_ai_redemption')
        path.write_text(json.dumps(facts), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'credit changed'):
            adapter.verify_case(self.context)
        self.port.date = DATE; self.port.day_calls = 0; self.run_case()
        Path(str(self.port.raw['path'])).write_text('Changed authored evidence', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            adapter.verify_case(self.context)

    def test_queued_news_or_toast_evidence_is_not_delivery_or_main_business_credit(self) -> None:
        self.port.evidence.append(self.port.note('optional-original-toast-unavailable.json'))
        facts = self.run_case()
        self.assertEqual(facts['observed_cells'], ['prefunded_publish'])
        self.assertIs(facts['toast_delivery_qualified'], False)
        self.assertIs(facts['product_release_pass'], False)

    def test_registry_uses_existing_public_adapter_and_independent_normal_close(self) -> None:
        registry = json.loads((REPO / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        cases = registry['products']['financial-markets']['cases']
        selected = next(row for row in cases if row['id'] == 'redemption-gui')
        self.assertEqual(sum(row['id'] == 'redemption-gui' for row in cases), 1)
        self.assertEqual(selected['adapter']['path'], '{repo_root}/tools/ck3_mod_acceptance_cases/generic_product_adapter.py')
        self.assertEqual(selected['normal_close']['reserve_seconds'], 180)
        self.assertIs(selected['normal_close']['actual_retained_OS0_and_original_native0_required'], True)
        self.assertIs(selected['whole_product_acceptance_credit'], False)
        for name in ('delisting-gui', 'futures-gui-transactions', 'clock-cadence-continuous14', 'lifecycle', 'news-crisis'):
            self.assertTrue(any(row['id'] == name for row in cases), name)


if __name__ == '__main__':
    unittest.main()
