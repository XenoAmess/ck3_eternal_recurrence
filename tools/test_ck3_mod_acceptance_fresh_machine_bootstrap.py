"""Real canonical ID round trips; no game, Steam, keeper, or account actions."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

import ck3_live_run_id as ids
from ck3_mod_acceptance_background_types import JsonObject, json_object
from ck3_mod_acceptance_fresh_machine_bootstrap import (
    FRESH_ADMISSION_MODE, FRESH_BOOTSTRAP_SCHEMA, MachineBinding,
    exact_pin, parse_bootstrap, require_empty_machine_history,
    validate_fresh_bootstrap, validate_frozen_fresh_admission,
)


class FreshMachineBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.binding = MachineBinding(
            machine_id='synthetic-fresh-machine', state_root=str(self.root/'ids'),
            admission_root=str(self.root/'ids/synthetic-fresh-machine/.shared-runtime-admissions-v1'))
        self.runtime = self.root/'runtime.json'
        self.manifest = self.root/'manifest.json'
        self.runtime.write_text('{}')
        self.manifest.write_text('{}')
        self.bundle: JsonObject = json_object({
            'schema': FRESH_BOOTSTRAP_SCHEMA, 'machine': self.binding,
            'runtime_config': exact_pin(self.runtime), 'runtime_manifest': exact_pin(self.manifest),
            'repo_root': str(self.root), 'bus_dir': str(self.root/'bus'),
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'maintenance_closures': [],
        })
        self.source = self.root/'fresh-bootstrap.json'
        self.save(self.source, self.bundle)
        self.events: list[JsonObject] = [
            {'schema': 'codex.task_bus.v1', 'sequence': 1, 'kind': 'registered',
             'summary': 'development task', 'resources': []}]
        self.packet: JsonObject = {'tasks': [{'resources': [], 'state': 'running'}]}
        self.inventory: JsonObject = {'blockers': [], 'process_absence_is_normal_exit_proof': False}

    def save(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def validate(self, previous_release: Path | None = None) -> JsonObject:
        return json_object(validate_fresh_bootstrap(
            self.bundle, bootstrap_path=self.source, binding=self.binding,
            runtime_path=self.runtime, manifest_path=self.manifest, repo_root=self.root,
            bus_dir=self.root/'bus', bus_events=self.events, bus_packet=self.packet,
            process_inventory=self.inventory, previous_release=previous_release))

    def test_actual_producer_consumer_json_round_trip_preserves_no_exit_claim(self) -> None:
        result = self.validate()
        self.assertEqual(result['mode'], FRESH_ADMISSION_MODE)
        self.assertIs(result['previous_normal_exit_claimed'], False)
        self.assertIs(result['business_pass'], False)
        self.assertEqual(parse_bootstrap(self.bundle), parse_bootstrap(json.loads(json.dumps(self.bundle))))

    def test_wrong_machine_runtime_and_local_bus_are_rejected(self) -> None:
        for field, value in [('machine', {**self.binding, 'machine_id': 'other-machine'}),
                             ('runtime_config', {**exact_pin(self.runtime), 'sha256': '0'*64}),
                             ('bus_dir', str(self.root/'unrelated-bus'))]:
            original = self.bundle[field]
            self.bundle[field] = json_object({'value': value})['value']
            self.save(self.source, self.bundle)
            with self.assertRaises(ValueError):
                self.validate()
            self.bundle[field] = original
            self.save(self.source, self.bundle)

    def test_prior_canonical_live_id_blocks_even_empty_artifacts_directory(self) -> None:
        ids.allocate_live_run_id('vanilla', machine_id=self.binding['machine_id'],
                                 state_root=Path(self.binding['state_root']))
        with self.assertRaisesRegex(ValueError, 'canonical live history'):
            self.validate()

    def test_empty_old_product_namespace_is_not_new_machine(self) -> None:
        (Path(self.binding['state_root'])/self.binding['machine_id']/'vanilla').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'canonical live history'):
            self.validate()

    def test_failed_global_admission_intent_cannot_be_reset(self) -> None:
        path = Path(self.binding['admission_root'])/'000001/intent.json'
        self.save(path, {'status': 'CONSUMED_ADMISSION_INTENT_NOT_RUN'})
        with self.assertRaisesRegex(ValueError, 'already consumed'):
            self.validate()

    def test_fictional_predecessor_field_and_argument_both_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, 'forbids every predecessor'):
            self.validate(self.root/'invented-release.json')
        self.bundle['previous_release'] = None
        with self.assertRaisesRegex(ValueError, 'no predecessor permitted'):
            self.validate()

    def test_shared_or_screen_history_blocks_even_when_now_released(self) -> None:
        self.events[0]['summary'] = 'product shared runtime acceptance'
        with self.assertRaisesRegex(ValueError, 'Existing live/screen history'):
            self.validate()
        self.events[0]['summary'] = 'old unrelated screen'
        self.events[0]['resources'] = ['ck3-screen:acquired']
        with self.assertRaisesRegex(ValueError, 'Existing live/screen history'):
            self.validate()

    def test_current_screen_or_game_controller_blocks(self) -> None:
        self.packet['tasks'] = [{'resources': ['ck3-screen:acquired']}]
        with self.assertRaisesRegex(ValueError, 'still owned'):
            self.validate()
        self.packet['tasks'] = [{'resources': []}]
        self.inventory['blockers'] = [{'pid': 77, 'name': 'ck3.exe'}]
        with self.assertRaisesRegex(ValueError, 'absence is not proven'):
            self.validate()

    def test_boolean_and_float_sequences_and_wrong_pin_types_refused(self) -> None:
        for bad in (True, 1.0, None, '1'):
            self.events[0]['sequence'] = bad
            with self.assertRaisesRegex(ValueError, 'sequence/schema'):
                self.validate()
        self.events[0]['sequence'] = 1
        self.bundle['runtime_config'] = json_object({**exact_pin(self.runtime), 'bytes': True})
        with self.assertRaisesRegex(ValueError, 'byte-count'):
            self.validate()

    def allocated_frozen(self) -> tuple[JsonObject, Path]:
        closure = self.validate()
        root = Path(self.binding['admission_root'])/'000001'
        root.mkdir(parents=True)
        self.save(root/'intent.json', {'closure': closure})
        identity = ids.allocate_live_run_id('vanilla', machine_id=self.binding['machine_id'],
                                            state_root=Path(self.binding['state_root']))
        live = self.root/'live'/identity.run_id
        live.mkdir(parents=True)
        self.save(root/'allocation.json', {'run_id': identity.run_id, 'live': str(live)})
        self.save(live/'predecessor-admission.json', {'closure': closure})
        frozen: JsonObject = json_object({
            'run_id': identity.run_id, 'initial_machine_no_predecessor': True,
            'previous_session_closed': False, 'previous_screen_released': False,
            'identity_allocation': {'machine_id': self.binding['machine_id'], 'state_root': self.binding['state_root']},
            'predecessor_admission': exact_pin(live/'predecessor-admission.json'),
        })
        return frozen, live

    def test_first_real_id_and_machine_record_are_required_for_launch(self) -> None:
        frozen, live = self.allocated_frozen()
        validate_frozen_fresh_admission(json_object(json.loads(json.dumps(frozen))), live)
        self.assertIs(frozen['previous_session_closed'], False)
        self.assertTrue((Path(self.binding['state_root'])/self.binding['machine_id']/'vanilla/allocations.jsonl').exists())

    def test_launch_refuses_fictional_previous_normal_exit_or_later_id(self) -> None:
        frozen, live = self.allocated_frozen()
        frozen['previous_session_closed'] = True
        with self.assertRaisesRegex(ValueError, 'Explicit first-machine'):
            validate_frozen_fresh_admission(frozen, live)
        frozen['previous_session_closed'] = False
        ids.allocate_live_run_id('vanilla', machine_id=self.binding['machine_id'],
                                 state_root=Path(self.binding['state_root']))
        with self.assertRaisesRegex(ValueError, 'sole actual run'):
            validate_frozen_fresh_admission(frozen, live)

    def test_fresh_claim_recheck_allows_only_machine_lock_metadata(self) -> None:
        root = Path(self.binding['admission_root'])
        root.mkdir(parents=True)
        (root/'chain.lock').write_bytes(b'0')
        self.save(root/'machine.json', self.binding)
        self.assertEqual(require_empty_machine_history(self.binding), self.binding)

    def add_maintenance(self) -> Path:
        task = 'steam-repair-maintenance'
        acquired: JsonObject = {'schema': 'codex.task_bus.v1', 'task_id': task, 'sequence': 2,
            'kind': 'registered', 'state': 'running', 'resources': ['ck3-screen:acquired'],
            'summary': 'maintenance-only:no-game-start:steam-core-file-validation'}
        released: JsonObject = {'schema': 'codex.task_bus.v1', 'task_id': task, 'sequence': 3,
            'kind': 'completed', 'state': 'done', 'resources': [],
            'summary': 'maintenance-only:no-game-start:steam-core-file-validation-released'}
        self.events.extend((acquired, released))
        original = self.root/'maintenance-registration.json'
        final = self.root/'maintenance-release.json'
        before = self.root/'maintenance-before.json'
        after = self.root/'maintenance-after.json'
        actions = self.root/'maintenance-actions.json'
        self.save(original, {'event': acquired, 'task': {'task_id': task, 'last_sequence': 2,
                   'state': 'running', 'resources': ['ck3-screen:acquired']}})
        head: JsonObject = {'task_id': task, 'last_sequence': 3, 'state': 'done', 'resources': []}
        self.save(final, {'event': released, 'task': head})
        self.packet['tasks'] = [head]
        inventory = {'machine_id': self.binding['machine_id'],
                     'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                     'tasklist_returncode': 0, 'tasklist_pids': [], 'wmi_pids': [], 'processes': []}
        self.save(before, inventory)
        self.save(after, inventory)
        self.save(actions, {'machine_id': self.binding['machine_id'],
                            'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                            'maintenance_only': True, 'no_game_start': True})
        closure = self.root/'maintenance-closure.json'
        self.save(closure, {'schema': 'ck3-mod-acceptance-maintenance-screen-closure-v1',
            'machine_id': self.binding['machine_id'], 'task_id': task,
            'maintenance_only': True, 'no_game_start': True,
            'registration': exact_pin(original), 'release': exact_pin(final),
            'before_inventory': exact_pin(before), 'after_inventory': exact_pin(after),
            'actions_result': exact_pin(actions)})
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        return closure

    def test_exact_released_maintenance_epoch_admits_without_claiming_game_exit(self) -> None:
        self.add_maintenance()
        result = self.validate()
        self.assertIs(result['prior_session_exists'], False)
        self.assertIs(result['previous_normal_exit_claimed'], False)
        evidence = result['maintenance_evidence']
        self.assertIsInstance(evidence, list)
        self.assertEqual(len(evidence) if isinstance(evidence, list) else 0, 6)

    def test_each_raw_maintenance_observation_requires_machine_utc_and_order(self) -> None:
        closure = self.add_maintenance()
        original_closure = json.loads(closure.read_text())
        for field in ('before_inventory', 'after_inventory', 'actions_result'):
            raw_path = Path(original_closure[field]['path'])
            original = json.loads(raw_path.read_text())
            for change in ({'machine_id': 'different-machine'}, {'observed_at_utc': None},
                           {'observed_at_utc': '2020-01-01T00:00:00'},
                           {'observed_at_utc': '2020-01-01T00:00:00+01:00'}):
                self.save(raw_path, {**original, **change})
                self.save(closure, {**original_closure, field: exact_pin(raw_path)})
                self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
                self.save(self.source, self.bundle)
                with self.assertRaises(ValueError):
                    self.validate()
            self.save(raw_path, original)
        self.save(closure, original_closure)
        after = Path(original_closure['after_inventory']['path'])
        self.save(after, {**json.loads(after.read_text()), 'observed_at_utc': '2020-01-01T00:00:00Z'})
        self.save(closure, {**original_closure, 'after_inventory': exact_pin(after)})
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        with self.assertRaisesRegex(ValueError, 'out of order'):
            self.validate()

    def test_declared_released_maintenance_preserves_unknown_raw_identity_without_exit_credit(self) -> None:
        closure = self.add_maintenance()
        raw = json.loads(closure.read_text())
        for field in ('before_inventory', 'after_inventory', 'actions_result'):
            original = Path(raw[field]['path'])
            self.save(original, {'historical_machine_id': 'unknown'})
            raw[field] = exact_pin(original)
        raw.update(schema='ck3-mod-acceptance-maintenance-screen-declaration-v1',
                   observed_at_utc=datetime.now(timezone.utc).isoformat(),
                   raw_observation_identity='unknown',
                   evidence_scope='declared-maintenance-not-previous-game-exit')
        self.save(closure, raw)
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        result = self.validate()
        self.assertIs(result['previous_normal_exit_claimed'], False)
        self.inventory['blockers'] = [{'pid': 77, 'name': 'ck3.exe'}]
        with self.assertRaisesRegex(ValueError, 'absence is not proven'):
            self.validate()
        self.inventory['blockers'] = []
        raw['raw_observation_identity'] = 'verified'
        self.save(closure, raw)
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        with self.assertRaisesRegex(ValueError, 'preserve unknown'):
            self.validate()

    def test_unreleased_maintenance_and_missing_declaration_and_game_history_refused(self) -> None:
        closure = self.add_maintenance()
        self.packet['tasks'] = [{'task_id': 'steam-repair-maintenance', 'last_sequence': 2,
                                'state': 'running', 'resources': ['ck3-screen:acquired']}]
        with self.assertRaisesRegex(ValueError, 'released head'):
            self.validate()
        self.packet['tasks'] = [{'task_id': 'steam-repair-maintenance', 'last_sequence': 3,
                                'state': 'done', 'resources': []}]
        raw = json.loads(closure.read_text())
        del raw['no_game_start']
        self.save(closure, raw)
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        with self.assertRaisesRegex(ValueError, 'Exact maintenance-only'):
            self.validate()
        raw['no_game_start'] = True
        self.save(closure, raw)
        self.bundle['maintenance_closures'] = json_object({'refs': [exact_pin(closure)]})['refs']
        self.save(self.source, self.bundle)
        ids.allocate_live_run_id('vanilla', machine_id=self.binding['machine_id'],
                                 state_root=Path(self.binding['state_root']))
        with self.assertRaisesRegex(ValueError, 'canonical live history'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
