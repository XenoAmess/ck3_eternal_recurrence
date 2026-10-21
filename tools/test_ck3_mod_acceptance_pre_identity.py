"""Actual failed-ID producer, preserved originals, retirement and first-ID consumer.

All state is temporary. No keeper, game, Steam, screen or account action runs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest

import ck3_live_run_id as ids
from ck3_mod_acceptance import Selection
from ck3_mod_acceptance_allocate import claim_machine_admission
from ck3_mod_acceptance_background_types import JsonObject, json_object
from ck3_mod_acceptance_fresh_machine_bootstrap import (
    create_bootstrap, create_pre_identity_request, exact_pin, fresh_ledger_path,
    require_empty_machine_history, retire_pre_identity_request, validate_pre_identity_request,
    validate_frozen_fresh_admission,
)
import test_ck3_mod_acceptance_fresh_machine_bootstrap as baseline


class PreIdentityRetirementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = baseline.FreshMachineBootstrapTests()
        self.env.setUp()
        self.addCleanup(self.env.doCleanups)
        self.root = self.env.root
        self.binding = self.env.binding
        self.tools = Path(__file__).resolve().parent
        self.state = self.root/'profiles/old'
        self.ledger = self.state.parent/'single-use-ledger'
        self.prepared = self.root/'prepared.json'
        self.env.save(self.env.runtime, {'manifest': exact_pin(self.env.manifest)})
        self.env.bundle['runtime_config'] = json_object(exact_pin(self.env.runtime))
        self.env.save(self.env.source, self.env.bundle)
        self.env.save(self.prepared, {'startup': {'state_dir': str(self.state)},
                                   'runtime_manifest': exact_pin(self.env.manifest)})
        self.selection = Selection.__new__(Selection)
        self.selection.runtime_path = self.env.runtime
        self.selection.manifest_path = self.env.manifest
        self.selection.prepared_path = self.prepared
        self.closure = self.env.validate()
        self.record = claim_machine_admission(self.binding, self.selection, argparse.Namespace(), self.closure)
        self.ledger.mkdir(parents=True)
        self.ledger_intent = self.ledger/'allocation-intent.json'
        self.env.save(self.ledger_intent, {
            'status': 'CONSUMED_ALLOCATION_INTENT_NOT_RUN', 'attempt': 'a01',
            'product': 'unregistered-preidentity-test', 'case': 'core',
            'prepared_case': exact_pin(self.prepared), 'machine_admission': str(self.record),
            'predecessor_admission': self.closure})
        self.operation = self.root/'operation'
        self.operation.mkdir()
        self.products = self.operation/'products.json'
        self.env.save(self.products, {'products': {'unregistered-preidentity-test': {
            'runtime_mod_key': 'unregistered-preidentity-test'}}})
        self.argv = [sys.executable, '-B', str(self.tools/'ck3_mod_acceptance.py'), 'allocate',
            '--runtime', str(self.env.runtime), '--products', str(self.products),
            '--product', 'unregistered-preidentity-test', '--case', 'core',
            '--prepared-case', str(self.prepared), '--attempt', 'a01',
            '--keeper-output', str(self.root/'keeper'), '--first-machine-bootstrap', str(self.env.source)]
        self.env.save(self.operation/'command.json', {'machine_id': self.binding['machine_id'],
            'observed_at_utc': self.env.inventory['observed_at_utc'], 'argv': self.argv})
        # Real terminal exception from the actual canonical allocator before identity.
        code = "from pathlib import Path;import ck3_live_run_id as i;i.allocate_live_run_id('unregistered-preidentity-test',state_root=Path("+repr(self.binding['state_root'])+"),machine_id="+repr(self.binding['machine_id'])+")"
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=self.tools,
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(result.returncode, 1)
        (self.operation/'stdout.json').write_text(result.stdout, encoding='utf-8')
        (self.operation/'stderr.log').write_text(result.stderr, encoding='utf-8')
        terminal = {'exit_code': result.returncode, 'output': json.dumps({'operation': str(self.operation)})+'\n'+result.stderr}
        self.env.save(self.operation/'event.json', {'payload': {'type': 'custom_tool_call_output',
            'output': [{'type': 'input_text', 'text': json.dumps(terminal)}]}})
        self.env.save(self.operation/'observation.json', {
            'schema': 'ck3-preidentity-root-tool-observation-v1', 'machine_id': self.binding['machine_id'],
            'observed_at_utc': self.env.inventory['observed_at_utc'],
            'observed_allocator_tool_exit_code': result.returncode,
            'extracted_original_event': exact_pin(self.operation/'event.json'),
            'historical_original_HANDLE_wait_claimed': False, 'normal_game_exit_claimed': False})
        self.request = self.operation/'request.json'
        self.refresh_request()

    def refresh_request(self) -> None:
        value = create_pre_identity_request(binding=self.binding, command=self.operation/'command.json',
            stdout=self.operation/'stdout.json', stderr=self.operation/'stderr.log',
            terminal_observation=self.operation/'observation.json', terminal_tool_event=self.operation/'event.json',
            machine_intent=self.record/'intent.json', ledger_intent=self.ledger_intent,
            id_source=self.tools/'ck3_live_run_id.py', products=self.products)
        self.env.save(self.request, value)

    def retire(self) -> None:
        retire_pre_identity_request(self.request, binding=self.binding, product='unregistered-preidentity-test',
            case='core', ledger_root=self.ledger, process_inventory=self.env.inventory,
            bus_events=self.env.events, bus_packet=self.env.packet, maintenance_closures=[])

    def test_actual_failure_retirement_first_id_and_frozen_consumer_round_trip(self) -> None:
        originals = {path: path.read_bytes() for path in (self.record/'intent.json', self.ledger_intent,
            self.operation/'stderr.log', self.operation/'event.json')}
        validate_pre_identity_request(self.request, self.binding)
        pending = create_bootstrap(binding=self.binding, runtime_path=self.env.runtime,
            manifest_path=self.env.manifest, repo_root=self.root, bus_dir=self.root/'bus',
            pending_pre_identity_retirement=self.request)
        self.assertEqual(pending['machine'], self.binding)
        with self.assertRaisesRegex(ValueError, 'already consumed'):
            require_empty_machine_history(self.binding)
        self.retire()
        self.retire()  # Same exact append-only retirement is idempotent before ID.
        self.assertEqual(require_empty_machine_history(self.binding), self.binding)
        next_ledger = fresh_ledger_path(self.binding, self.ledger)
        self.assertEqual(next_ledger, self.ledger/'pre-identity-epoch-000002')
        closure = self.env.validate()
        next_record = claim_machine_admission(self.binding, self.selection, argparse.Namespace(), closure)
        self.assertEqual(next_record.name, '000002')
        next_ledger.mkdir()
        self.env.save(next_ledger/'allocation-intent.json', {'status': 'new-consumed-intent'})
        identity = ids.allocate_live_run_id('vanilla', state_root=Path(self.binding['state_root']),
                                          machine_id=self.binding['machine_id'])
        self.assertIn('-R0001', identity.run_id)
        live = self.root/'live'/identity.run_id
        live.mkdir(parents=True)
        self.env.save(next_record/'allocation.json', {'run_id': identity.run_id, 'live': str(live)})
        self.env.save(live/'predecessor-admission.json', {'closure': closure})
        frozen = json_object({'run_id': identity.run_id, 'initial_machine_no_predecessor': True,
            'previous_session_closed': False, 'previous_screen_released': False,
            'identity_allocation': {'machine_id': self.binding['machine_id'], 'state_root': self.binding['state_root']},
            'predecessor_admission': exact_pin(live/'predecessor-admission.json')})
        validate_frozen_fresh_admission(json_object(json.loads(json.dumps(frozen))), live)
        for path, raw in originals.items():
            self.assertEqual(path.read_bytes(), raw)
        marker = json_object(json.loads((self.record/'retired-pre-identity.json').read_text()))
        for field in ('canonical_id_allocated', 'normal_exit_proven', 'business_pass'):
            self.assertIs(marker[field], False)

    def test_request_machine_changed_original_and_missing_tool_terminal_rejected(self) -> None:
        request = json_object(json.loads(self.request.read_text()))
        request['machine'] = json_object({**self.binding, 'machine_id': 'wrong-machine'})
        self.env.save(self.request, request)
        with self.assertRaisesRegex(ValueError, 'canonical ID namespace|another actual machine'):
            self.retire()
        self.refresh_request()
        (self.operation/'stderr.log').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            self.retire()
        self.refresh_request()
        with self.assertRaisesRegex(ValueError, 'exact pre-ID'):
            self.retire()

    def test_existing_canonical_id_allocation_keeper_and_runtime_block(self) -> None:
        for path in (self.record/'allocation.json', self.root/'keeper', self.state/'control'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}')
            with self.assertRaises(ValueError):
                self.retire()
            path.unlink()
        self.env.packet['tasks'] = [{'resources': ['ck3-screen:acquired']}]
        with self.assertRaisesRegex(ValueError, 'still owned'):
            self.retire()
        self.env.packet['tasks'] = []
        ids.allocate_live_run_id('vanilla', state_root=Path(self.binding['state_root']),
                                 machine_id=self.binding['machine_id'])
        with self.assertRaisesRegex(ValueError, 'canonical ID namespace'):
            self.retire()

    def test_bool_exit_or_invented_handle_exit_is_not_terminal_evidence(self) -> None:
        observation = json_object(json.loads((self.operation/'observation.json').read_text()))
        for field, bad in (('observed_allocator_tool_exit_code', True),
                           ('historical_original_HANDLE_wait_claimed', True), ('normal_game_exit_claimed', True)):
            changed = {**observation, field: bad}
            self.env.save(self.operation/'observation.json', changed)
            self.refresh_request()
            with self.assertRaisesRegex(ValueError, 'tool-exit-only'):
                self.retire()
        self.env.save(self.operation/'observation.json', observation)
        self.env.save(self.operation/'event.json', {'payload': {'type': 'custom_tool_call_output', 'output': []}})
        observation['extracted_original_event'] = json_object(exact_pin(self.operation/'event.json'))
        self.env.save(self.operation/'observation.json', observation)
        self.refresh_request()
        with self.assertRaisesRegex(ValueError, 'Exactly one original'):
            self.retire()

    def test_early_public_allocator_key_validation_consumes_no_intents(self) -> None:
        before = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        code = "from pathlib import Path;import argparse;from ck3_mod_acceptance import Selection;from ck3_mod_acceptance_allocate import _allocate_and_keep_impl;s=Selection.__new__(Selection);s.prepared_path=Path('unused');s.context={};s.product={'runtime_mod_key':'unregistered-preidentity-test'};s.product_key='unregistered-preidentity-test';_allocate_and_keep_impl(s,argparse.Namespace())"
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=self.tools,
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown mod key 'unregistered-preidentity-test'", result.stderr)
        self.assertNotIn('AttributeError', result.stderr)
        after = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.record/'retired-pre-identity.json').exists())


if __name__ == '__main__':
    unittest.main()
