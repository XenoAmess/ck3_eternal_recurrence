"""Actual generic prepare fragment/run/verify, authored Root/transport IO, no Game.

Authored archive confirmations below test consumer rejection/retention only. They
are not CK3 saves, actual fills, production financial-script execution or live credit.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from ck3_mod_acceptance_background_types import CONTINUOUS14_PASSIVE_STORY_TYPES_V1, JsonObject, json_object
from ck3_mod_acceptance_cases import generic_product_adapter as adapter

CONFIG = REPO / 'tools/ck3_mod_acceptance_cases/financial_markets_futures_gui_transactions.json'
DATE = 53146992  # Date used as a software stimulus, matching the retained producer metadata.

# Exact parsed R37 archive metadata retained from the real producer; see SOURCEPINS.
# No historical SAVE path is opened by this software consumer test.
ACTUAL_R37_ARCHIVE = json.loads(r'''{
  "schema": "ck3-financial-checkpoint-archive-v1",
  "machine_id": "4-8e1c2f1861",
  "captured_at_utc": "2026-11-20T05:14:24.269405+00:00",
  "request": {
    "path": "C:\\workspace\\ck3-market-task-20261118\\continuous14-terminal01-archive-author\\archive-request.json",
    "bytes": 600,
    "sha256": "5d43ef34796a6658fbda1d303e2b4c555e8fc377e3359e30abc0a2aada54c722"
  },
  "original_checkpoint_receipt": {
    "path": "C:\\workspace\\ck3-market-task-20261118\\continuous14-terminal01-archive-author\\native-report.original.json",
    "bytes": 1051316,
    "sha256": "3ea1d13623da82ee7a1e1f073c3bd4318c95257f127c49cf1a5cfc385837e11f"
  },
  "result_json_pointer": "/steps/3/result",
  "date_raw": 53146992,
  "original_checkpoint_result": {
    "schema": "ck3_1210_full_clock_control_result_v1",
    "game_version": "1.21.0",
    "executable_sha256": "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC",
    "adapter_id": "ck3-1.21.0-msvc-x64",
    "backend": "ck3-1.21.0-native-headless-main-thread",
    "step": "save-checkpoint",
    "accepted": true,
    "queue_status": "submitted",
    "effect_attempted": true,
    "full_snapshot_before_verified": true,
    "complete_snapshot": false,
    "physical_save_confirmed": false,
    "save_name": "xar_checkpoint",
    "status": "submitted",
    "submission": {
      "sequence": 2,
      "requested_save_name": "xar_checkpoint",
      "date_raw": 53146992
    },
    "backend_id": "native-headless",
    "checkpoint": {
      "status": "saved",
      "path": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\profile\\save games\\xar_checkpoint.ck3",
      "name": "xar_checkpoint.ck3",
      "size": 176057389,
      "sha256": "6188a8912aca3369840739f55578b71eb1e1fc0408996ec74a0d385e595a4140",
      "date_raw": 53146992,
      "overwrite_confirmed": true,
      "strategy": "native-autosave-command-v1",
      "episode_projection": "native_campaign",
      "succession_lifecycle": null,
      "history_index": 113,
      "episode_character_id": null,
      "episode_run_id": null
    },
    "episode_seed": null,
    "materialization": {
      "available": true,
      "save_dir": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\profile\\save games",
      "mtime_ns": 1795151645028030200
    },
    "driver_state_replace_receipt": {
      "scope": "WRITE_REPLACE_RETURNED_NOT_FSYNC",
      "status": "unconfirmed",
      "write_replace_returned": true,
      "save_binding_verified": false,
      "reason": "save_binding_mismatch",
      "attempt_binding": {
        "pipe_name": "\\\\.\\pipe\\ck3_mod_acceptance_4-8e1c2f1861--financial-markets--R0037",
        "bridge_pid": 17692,
        "episode_character_id": null,
        "episode_run_id": null,
        "succession_lifecycle": {
          "schema": "xar.ck3.succession-lifecycle-binding/v1",
          "lifecycle": "rogue_one_life",
          "xar_enabled": "xar_on",
          "pact_contract": "terminal_settlement_required",
          "source": "legacy-driver-default",
          "environment_sha256": null
        },
        "campaign_goal": null
      },
      "binding_contract": "one_life_episode_identity_v1",
      "checkpoint_episode_projection": "native_campaign",
      "missing_checkpoint_binding_fields": [
        "episode_character_id",
        "episode_run_id"
      ],
      "recorded_session_binding": {
        "pipe_name": "\\\\.\\pipe\\ck3_mod_acceptance_4-8e1c2f1861--financial-markets--R0037",
        "bridge_pid": 17692,
        "episode_character_id": null,
        "episode_run_id": null
      },
      "save_history_index": 113,
      "checkpoint": {
        "status": "saved",
        "path": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\profile\\save games\\xar_checkpoint.ck3",
        "name": "xar_checkpoint.ck3",
        "size": 176057389,
        "sha256": "6188a8912aca3369840739f55578b71eb1e1fc0408996ec74a0d385e595a4140",
        "date_raw": 53146992,
        "overwrite_confirmed": true,
        "strategy": "native-autosave-command-v1",
        "episode_projection": "native_campaign",
        "succession_lifecycle": null,
        "history_index": 113,
        "episode_character_id": null,
        "episode_run_id": null
      },
      "encoded_history_rows": 113,
      "driver_state_path": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\native-session\\driver-state.json"
    }
  },
  "requested_source_path": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\profile\\save games\\xar_checkpoint.ck3",
  "source": {
    "path": "C:\\workspace\\ck3-market-live-20261120c\\managed-states\\financial-continuous14d\\state\\profile\\save games\\xar_checkpoint.ck3",
    "bytes": 176057389,
    "sha256": "6188a8912aca3369840739f55578b71eb1e1fc0408996ec74a0d385e595a4140"
  },
  "source_facts_before": {
    "device": 11562708564543669174,
    "inode": 281474980545974,
    "bytes": 176057389,
    "mtime_ns": 1795151645028030200,
    "ctime_ns": 1795151374836576200,
    "birthtime_ns": 1795151374836576200
  },
  "source_facts_after": {
    "device": 11562708564543669174,
    "inode": 281474980545974,
    "bytes": 176057389,
    "mtime_ns": 1795151645028030200,
    "ctime_ns": 1795151374836576200,
    "birthtime_ns": 1795151374836576200
  },
  "archive": {
    "path": "C:\\workspace\\ck3-market-task-20261118\\financial-physical-saves-continuous02\\continuous14-terminal01\\xar_checkpoint.ck3",
    "bytes": 176057389,
    "sha256": "6188a8912aca3369840739f55578b71eb1e1fc0408996ec74a0d385e595a4140"
  },
  "archive_facts": {
    "device": 11562708564543669174,
    "inode": 281474980546292,
    "bytes": 176057389,
    "mtime_ns": 1795151662005298600,
    "ctime_ns": 1795151661873708700,
    "birthtime_ns": 1795151661873708700
  },
  "same_file": false,
  "exact_copy": true,
  "budget_before": {
    "limit_bytes": 3221225472,
    "scope": "scene plus dedicated external archive-parent logical regular-file bytes; reparse targets excluded; not allocated disk size or a future concurrent-write reservation",
    "scene": {
      "root": "C:\\workspace\\ck3-market-live-20261120c",
      "regular_file_bytes": 1330824525,
      "regular_files": 4961,
      "reparse_targets_not_followed": []
    },
    "external_archive": {
      "root": "C:\\workspace\\ck3-market-task-20261118\\financial-physical-saves-continuous02",
      "regular_file_bytes": 164325810,
      "regular_files": 2,
      "reparse_targets_not_followed": []
    },
    "counted_bytes": 1495150335
  },
  "budget_after_copy": {
    "limit_bytes": 3221225472,
    "scope": "scene plus dedicated external archive-parent logical regular-file bytes; reparse targets excluded; not allocated disk size or a future concurrent-write reservation",
    "scene": {
      "root": "C:\\workspace\\ck3-market-live-20261120c",
      "regular_file_bytes": 1330889875,
      "regular_files": 4961,
      "reparse_targets_not_followed": []
    },
    "external_archive": {
      "root": "C:\\workspace\\ck3-market-task-20261118\\financial-physical-saves-continuous02",
      "regular_file_bytes": 340383199,
      "regular_files": 3,
      "reparse_targets_not_followed": []
    },
    "counted_bytes": 1671273074
  },
  "metadata_reserve_bytes": 16384,
  "source_open_mode": "rb",
  "target_open_mode": "xb",
  "SAVE_invoked": false,
  "live_profile_written": false,
  "financialCertified": false,
  "cold_load_proven": false
}''')


def file_pin(path: Path) -> JsonObject:
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class Port:
    """Only Root/file/transport ports; the adapter's real phase loop is unchanged."""
    def __init__(self, root: Path, context: JsonObject, config: JsonObject) -> None:
        self.root, self.context, self.config = root, context, config
        self.requests: list[str] = []
        self.date_shift = False
        self.day_calls = 0
        self.baseline = self.archive('baseline')
        self.after = self.archive('after-long-and-leverage')
        self.query = self.note('gui-query.json')
        self.activation = self.note('gui-activation.json')
        self.audit = self.note('audit.json')
        self.raw = self.note('raw.json')
        self.evidence = [self.baseline, self.after, self.query, self.activation, self.audit, self.raw]
        self.physical_archives = [self.baseline]
        self.cells: JsonObject = {name: {'status': 'NOT_OBSERVED', 'reason': 'No real software transport fill is claimed', 'evidence': []}
                                 for name in adapter.FUTURES_GUI_TRANSACTION_CELLS}

    def note(self, name: str) -> JsonObject:
        path = self.root / name
        path.write_text(json.dumps({'authored_no_game_input': name}), encoding='utf-8')
        return file_pin(path)

    def archive(self, name: str) -> JsonObject:
        source = self.root / (name + '-source.ck3')
        source.write_text('AUTHORED SOFTWARE INPUT ONLY ' + name, encoding='utf-8')
        save = self.root / (name + '.ck3')
        save.write_bytes(source.read_bytes())
        path = self.root / (name + '.archive.json')
        receipt = copy.deepcopy(ACTUAL_R37_ARCHIVE)
        receipt.update(source=file_pin(source), archive=file_pin(save), date_raw=DATE)
        native = receipt['original_checkpoint_result']
        native['checkpoint'].update(path=str(source.resolve()), size=save.stat().st_size,
            sha256=file_pin(save)['sha256'], date_raw=DATE)
        # Preserve actual Native physical_save_confirmed=false, SDK saved and
        # materialization.available=true; these are separate producer facts.
        path.write_text(json.dumps(receipt), encoding='utf-8')
        return file_pin(path)

    def observe(self, name: str) -> None:
        if self.after not in self.physical_archives:
            self.physical_archives.append(self.after)
        assertions = {key: True for key in adapter.FUTURES_GUI_COMMON_ASSERTIONS}
        assertions[adapter.FUTURES_GUI_CELL_ASSERTIONS[name]] = True
        self.cells[name] = {'status': 'OBSERVED', 'assertions': assertions,
            'before_archive': self.baseline, 'after_archive': self.after,
            'gui_actions': [{'query': self.query, 'activation': self.activation}], 'audit': self.audit, 'raw': self.raw}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> JsonObject:
        if allow_actor_change:
            raise AssertionError('This case never grants actor transitions')
        return {'date_raw': DATE + (24 if self.date_shift and self.requests else 0), 'paused': True,
                'active_event': None, 'pending_character_interaction': None}

    def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90) -> JsonObject:
        if reserve != 90:
            raise AssertionError('Original Root close reserve changed')
        self.requests.append(name)
        required = request['required_assertions']
        if not isinstance(required, list):
            raise AssertionError('Actual adapter request required')
        result: JsonObject = {'run_id': self.context['run_id'], 'reviewer': '/root',
            'assertions': {str(key): True for key in required}, 'evidence': self.evidence}
        if name == 'bind-current-financial-baseline':
            result.update(baseline_archive=self.baseline, baseline_audit=self.audit, baseline_raw=self.raw)
        elif name == 'normal-gui-transactions-and-saved-reconciliation':
            result['futures_gui_transactions'] = self.cells
            result['physical_archives'] = self.physical_archives
        else:
            raise AssertionError('No extra phase is required by this paused case')
        return result

    def checkpoint(self, name: str, value: JsonObject) -> Path:
        path = self.root / (name + '.json')
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def log_bytes(self) -> bytes:
        return b''  # No fake product PASS/fixture ARM marker.

    def advance_day(self, *args: object, **kwargs: object) -> JsonObject:
        self.day_calls += 1
        raise AssertionError('Zero-day case must never enter any day/sentinel route')

    def execute_plan(self, *args: object, **kwargs: object) -> JsonObject:
        raise AssertionError('No hidden Host, native setter, business effect or automatic GUI execution')


class FuturesGuiTransactionsCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix='futures-gui-case-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = json_object(json.loads(CONFIG.read_bytes()))
        self.context: JsonObject = {'product': 'financial-markets', 'case': 'futures-gui-transactions',
            'case_contract': self.config, 'run_id': 'authored-only-current-run', 'output': str(self.root),
            'state_dir': str(self.root), 'case_spec': {'budgets': {'command_timeout': 300}},
            'case_inputs': {'post_start': {'government_key': 'feudal_government', 'primary_title_tier_key': 'duchy', 'independent': True}}}
        profile = self.root / 'profile'
        for relative in ('mod/product.mod', 'mod/fixture.mod', 'mod-content/product/descriptor.mod'):
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('name="Authored profile only"', encoding='utf-8')
        (profile / 'dlc_load.json').write_text(json.dumps({'enabled_mods': ['mod/product.mod', 'mod/fixture.mod']}), encoding='utf-8')
        compiled: JsonObject = {'schema': 'ck3-mod-acceptance-product-assertions-v1', 'product': 'financial-markets',
            'case': 'futures-gui-transactions', 'config': adapter.resolve_post_start(self.context)['case_contract'], 'required_markers': [], 'product_marker_minimum': {}}
        path = profile / 'mod-content/fixture/_case_contract.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(compiled), encoding='utf-8')
        self.port = Port(self.root, self.context, self.config)

    def run_actual(self) -> JsonObject:
        return adapter.run_case(self.context, self.port)  # Actual production adapter, not a copied phase loop.

    def test_two_zero_day_phases_execute_and_joint_long_leverage_checkpoint_gets_only_local_credit(self) -> None:
        self.port.observe('long'); self.port.observe('leverage_selection')
        facts = self.run_actual()
        self.assertEqual(self.port.requests, [row['id'] for row in self.config['gui_phases']])
        self.assertEqual(self.port.day_calls, 0)
        self.assertEqual(facts['observed_cells'], ['long', 'leverage_selection'])
        self.assertEqual(facts['retained_physical_checkpoint_count'], 2)
        verified = adapter.verify_case(self.context)
        self.assertEqual(verified['observed_cells'], facts['observed_cells'])
        for key in ('business_pass', 'product_release_pass', 'derivatives_acceptance_pass', 'financial_clock_qualified'):
            self.assertIs(verified[key], False)
        self.assertNotIn('normal_close_qualified', verified)  # Existing shared postclose owns this gate.

    def test_no_qualification_or_no_fill_remains_not_observed_without_advancing_or_requiring_arm(self) -> None:
        facts = self.run_actual()
        self.assertEqual(facts['observed_cells'], [])
        self.assertEqual(facts['not_observed_cells'], list(adapter.FUTURES_GUI_TRANSACTION_CELLS))
        self.assertEqual(facts['natural_days_advanced'], 0)
        self.assertEqual(self.port.day_calls, 0)
        self.assertIs(facts['business_pass'], False)

    def test_actual_prepare_catalog_fragment_carries_only_exact_passive_legacy_types(self) -> None:
        tree = ast.parse(Path(adapter.__file__).read_bytes())
        prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_prepare_fixture_case')
        definitions = [node for node in prepare.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'futures_gui' for target in node.targets)]
        writers = [node for node in ast.walk(prepare) if isinstance(node, ast.If)
            and isinstance(node.test, ast.Name) and node.test.id == 'futures_gui']
        self.assertEqual(len(definitions), 1); self.assertEqual(len(writers), 1)
        actual = compile(ast.fix_missing_locations(ast.Module(body=[*definitions, *writers], type_ignores=[])), str(adapter.__file__), 'exec')
        fixture = self.root / 'actual-passive-writer'; fixture.mkdir()
        namespace: dict[str, object] = {'context': self.context, 'config': self.config, 'fixture': fixture,
            'json_object': adapter.json_object, '_futures_gui_transactions_enabled': adapter._futures_gui_transactions_enabled}
        exec(actual, namespace)
        output = fixture / 'common/story_cycles/xfma_futures_gui_passive.txt'
        expected = ''.join(name + ' = { visible = no }\n' for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1)
        self.assertEqual(output.read_text(encoding='utf-8-sig'), expected)
        self.assertEqual([p.relative_to(fixture).as_posix() for p in fixture.rglob('*') if p.is_file()],
                         ['common/story_cycles/xfma_futures_gui_passive.txt'])
        for forbidden in ('effect', 'on_action', 'on_start', 'log', 'timer', 'xfma_armed', 'set_variable'):
            self.assertNotIn(forbidden, expected)
        wrong = copy.deepcopy(self.config); wrong['passive_story_types'] = [*CONTINUOUS14_PASSIVE_STORY_TYPES_V1, 'xfma_unknown_e999']
        with self.assertRaises(ValueError):
            adapter._futures_gui_transactions_enabled(json_object({**self.context, 'case_contract': wrong}))

    def test_exact_case_and_integer_zero_bounds_reject_cross_case_or_widening(self) -> None:
        for field, value in [('maximum_natural_days', True), ('maximum_natural_days', 1),
                             ('allow_actor_change', True), ('fixture_emitter', {}), ('clock_purpose', 'continuous14_diagnostic')]:
            with self.subTest(field=field, value=value):
                config = copy.deepcopy(self.config); config[field] = value
                with self.assertRaises(ValueError):
                    adapter._futures_gui_transactions_enabled(json_object({**self.context, 'case_contract': config}))
        with self.assertRaises(ValueError):
            adapter._futures_gui_transactions_enabled(json_object({**self.context, 'case': 'derivatives'}))
        for value in (6.0, True):
            config = copy.deepcopy(self.config)
            contract = json_object(config['futures_gui_transactions_contract']); contract['physical_save_maximum'] = value
            config['futures_gui_transactions_contract'] = contract
            with self.assertRaises(ValueError):
                adapter._futures_gui_transactions_enabled(json_object({**self.context, 'case_contract': config}))

    def test_observed_cell_without_real_receipt_set_or_exact_accounting_review_is_rejected(self) -> None:
        self.port.observe('long')
        cell = json_object(self.port.cells['long']); cell.pop('raw')
        self.port.cells['long'] = cell
        with self.assertRaises(ValueError):
            self.run_actual()
        self.assertFalse((self.root / 'generic-product-case-result.json').exists())

    def test_observed_cell_false_accounting_assertion_is_not_converted_to_credit(self) -> None:
        self.port.observe('add_margin')
        cell = json_object(self.port.cells['add_margin']); assertions = json_object(cell['assertions'])
        assertions['actual_margin_fees_cash_counterparty_and_unrelated_assets_independently_reconciled'] = False
        cell['assertions'] = assertions; self.port.cells['add_margin'] = cell
        with self.assertRaises(ValueError):
            self.run_actual()

    def test_reused_single_archive_or_cross_day_archive_cannot_prove_observed_operation(self) -> None:
        self.port.observe('withdraw_margin')
        cell = json_object(self.port.cells['withdraw_margin']); cell['after_archive'] = self.port.baseline
        self.port.cells['withdraw_margin'] = cell
        with self.assertRaises(ValueError):
            self.run_actual()
        self.port.observe('withdraw_margin')
        path = Path(str(self.port.after['path'])); receipt = json.loads(path.read_bytes()); receipt['date_raw'] = DATE + 24
        path.write_text(json.dumps(receipt), encoding='utf-8')
        self.port.after = file_pin(path); self.port.evidence[1] = self.port.after; self.port.observe('withdraw_margin')
        with self.assertRaises(ValueError):
            self.run_actual()

    def test_root_phase_date_advance_fails_existing_zero_day_loop_before_day_dispatch(self) -> None:
        self.port.date_shift = True
        with self.assertRaisesRegex(ValueError, 'calendar bound'):
            self.run_actual()
        self.assertEqual(self.port.day_calls, 0)

    def test_verify_rechecks_original_evidence_and_cell_statuses(self) -> None:
        self.port.observe('reduce'); self.run_actual()
        Path(str(self.port.raw['path'])).write_text('changed after original Root response', encoding='utf-8')
        with self.assertRaises(ValueError):
            adapter.verify_case(self.context)

    def test_registered_case_keeps_old_derivatives_and_clock_contracts_unmodified(self) -> None:
        registry = json.loads((REPO / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        indexed = {row['id']: row for row in registry['products']['financial-markets']['cases']}
        new = indexed['futures-gui-transactions']
        self.assertEqual(new['adapter']['path'], '{repo_root}/tools/ck3_mod_acceptance_cases/generic_product_adapter.py')
        self.assertEqual(new['normal_close'], indexed['cold-reload']['normal_close'])
        self.assertFalse(new['whole_product_acceptance_credit'])
        for filename, days in [('financial_markets_derivatives.json', 14), ('financial_markets_cold_reload.json', 0),
                               ('financial_markets_clock_cadence_continuous14.json', 14)]:
            config = json_object(json.loads((CONFIG.parent / filename).read_bytes()))
            self.assertEqual(config['maximum_natural_days'], days)
            self.assertFalse(adapter._futures_gui_transactions_enabled(json_object({
                'product': 'financial-markets', 'case': config['case_id'], 'case_contract': config})))


    def test_actual_r37_sdk_checkpoint_shape_keeps_native_false_and_rejects_incomplete_materialization(self) -> None:
        path = self.root / 'actual-r37-archive-metadata.json'
        path.write_text(json.dumps(ACTUAL_R37_ARCHIVE), encoding='utf-8')
        reference = file_pin(path)
        phase: JsonObject = {'evidence': [reference]}
        saved = adapter._futures_gui_archive(reference, phase, DATE)
        self.assertEqual(saved['sha256'], ACTUAL_R37_ARCHIVE['archive']['sha256'])
        self.assertIs(ACTUAL_R37_ARCHIVE['original_checkpoint_result']['physical_save_confirmed'], False)
        for defect in ('not-accepted', 'not-saved', 'not-materialized', 'size', 'sha', 'date', 'same-file'):
            with self.subTest(defect=defect):
                changed = copy.deepcopy(ACTUAL_R37_ARCHIVE)
                native = changed['original_checkpoint_result']
                if defect == 'not-accepted': native['accepted'] = False
                elif defect == 'not-saved': native['checkpoint']['status'] = 'submitted'
                elif defect == 'not-materialized': native['materialization']['available'] = False
                elif defect == 'size': native['checkpoint']['size'] += 1
                elif defect == 'sha': native['checkpoint']['sha256'] = '0' * 64
                elif defect == 'date': native['checkpoint']['date_raw'] += 24
                else: changed['same_file'] = True
                path.write_text(json.dumps(changed), encoding='utf-8')
                current = file_pin(path)
                with self.assertRaises(ValueError):
                    adapter._futures_gui_archive(current, {'evidence': [current]}, DATE)

    def test_distinct_receipt_aliases_of_same_archived_save_cannot_count_as_two_endpoints(self) -> None:
        self.port.observe('long')
        alias = self.root / 'second-receipt-same-physical-archive.json'
        alias.write_bytes(Path(str(self.port.baseline['path'])).read_bytes())
        other = file_pin(alias); self.port.evidence.append(other)
        cell = json_object(self.port.cells['long']); cell['after_archive'] = other
        self.port.cells['long'] = cell
        with self.assertRaisesRegex(ValueError, 'checkpoint'):
            self.run_actual()

    def test_real_saved_prepare_engine_json_to_public_run_and_verify_resolves_only_null_post_start(self) -> None:
        from test_continuous14_clock_diagnostic import Continuous14PrepareJsonBoundaryTests
        import ck3_mod_acceptance_prepare as preparation
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='futures-real-prepare-') as directory:
            context = Continuous14PrepareJsonBoundaryTests().context(Path(directory))
            context.update(product='financial-markets', case='futures-gui-transactions', case_contract=copy.deepcopy(self.config),
                run_id='authored-only-current-run', case_spec={'budgets': {'command_timeout': 300}})
            context['saved_campaign']['date_raw'] = DATE
            source_contract = copy.deepcopy(context['case_contract'])
            with patch.object(preparation, '_engine', wraps=preparation._engine) as actual_engine:
                prepared = adapter.prepare_case(context)
            self.assertGreaterEqual(actual_engine.call_count, 1)
            self.assertEqual(json.loads(json.dumps(prepared)), prepared)
            compiled, _ = adapter.compiled_contract(context)
            self.assertEqual(compiled['config']['post_start'], context['case_inputs']['post_start'])
            self.assertEqual(context['case_contract'], source_contract)
            self.assertTrue(all(value is None for value in source_contract['post_start'].values()))
            profile = Path(prepared['profile_preparation']['profile'])
            passive = profile / 'mod-content/fixture/common/story_cycles/xfma_futures_gui_passive.txt'
            self.assertEqual(passive.read_text(encoding='utf-8-sig'), ''.join(
                name + ' = { visible = no }\n' for name in CONTINUOUS14_PASSIVE_STORY_TYPES_V1))
            port = Port(Path(context['output']), json_object(context), self.config)
            facts = adapter.run_case(context, port)
            self.assertEqual(port.day_calls, 0)
            self.assertEqual(len(port.requests), 2)
            self.assertEqual(adapter.verify_case(context)['observed_cells'], [])
            self.assertEqual(context['case_contract'], source_contract)
            self.assertFalse(facts['business_pass'])
            # The original resolver's non-null no-overwrite rule remains active.
            context['case_contract']['post_start']['government_key'] = 'feudal_government'
            context['case_inputs']['post_start']['government_key'] = 'clan_government'
            with self.assertRaisesRegex(ValueError, 'Cannot overwrite'):
                adapter.run_case(context, port)
            with self.assertRaisesRegex(ValueError, 'Cannot overwrite'):
                adapter.verify_case(context)



    def test_unfilled_attempt_checkpoint_still_consumes_archive_slot_without_business_credit(self) -> None:
        self.port.physical_archives.append(self.port.after)
        self.port.cells['long'] = {'status': 'NOT_OBSERVED', 'reason': 'Actual order still unfilled',
                                   'evidence': [self.port.query, self.port.activation, self.port.after]}
        facts = self.run_actual()
        self.assertEqual(facts['retained_physical_checkpoint_count'], 2)
        self.assertEqual(facts['observed_cells'], [])
        self.assertFalse(facts['business_pass'])

    def test_seventh_actual_checkpoint_is_rejected_even_if_every_cell_is_not_observed(self) -> None:
        for number in range(6):
            reference = self.port.archive('unfilled-save-' + str(number))
            self.port.evidence.append(reference)
            self.port.physical_archives.append(reference)
        with self.assertRaisesRegex(ValueError, 'six-archive'):
            self.run_actual()
        self.assertFalse((self.root / 'generic-product-case-result.json').exists())


if __name__ == '__main__':
    unittest.main()
