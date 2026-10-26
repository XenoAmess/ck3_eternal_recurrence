"""Exercise allocated-unrun recovery again under the actual machine writer lock."""
from __future__ import annotations

import argparse
from contextlib import AbstractContextManager, ExitStack, contextmanager
import json
from pathlib import Path
from typing import Callable, Iterator, Protocol, runtime_checkable
import unittest
from unittest.mock import patch

import ck3_live_run_id as ids
import ck3_mod_acceptance_allocate as allocator
import ck3_mod_acceptance_unrun as unrun
from ck3_mod_acceptance import Selection
from ck3_mod_acceptance_background_types import JsonObject, file_pin, json_object, object_field, text_field
from ck3_mod_acceptance_fresh_machine_bootstrap import MachineBinding
from test_ck3_mod_acceptance_unrun_stages import RootAllocatorTripletTests


@runtime_checkable
class LockProvider(Protocol):
    def __call__(self, path: Path) -> AbstractContextManager[object]: ...


class PrelaunchUnrunWriterAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = RootAllocatorTripletTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        bundle, self.live, self.keeper, _ = fixture.prelaunch_fixture()
        self.bundle = json_object(bundle)
        self.close = fixture.root / 'closure.json'
        self.close.write_text(json.dumps(bundle), encoding='utf-8')
        self.freeze = json_object(json.loads((self.live / 'frozen-argv.json').read_text(encoding='utf-8')))
        self.release_path = Path(file_pin(self.bundle['admin_done'])['path'])
        provider: object = allocator
        if not isinstance(provider, allocator._TTLAdmissionEvidence):
            raise AssertionError('Actual shared recovery evidence provider unavailable')
        release_value: object = provider.read_failed_runtime_release(self.release_path)
        self.release = json_object(release_value)
        self.packet: JsonObject = {'tasks': [{**object_field(self.release, 'task'), 'age_seconds': 0, 'stale': False}]}
        self.inventory: JsonObject = {'blockers': []}
        self.next_state = fixture.root / 'new-state'
        self.args = argparse.Namespace(previous_live=self.live, previous_keeper=self.keeper,
            previous_failure_close=self.close, previous_release=self.release_path)
        self.selection = object.__new__(Selection)
        self.selection.state_dir = self.next_state
        self.selection.runtime_path = fixture.root / 'runtime.json'
        self.selection.manifest_path = fixture.root / 'manifest.json'
        self.selection.prepared_path = fixture.root / 'next-prepared.json'
        self.selection.runtime = {'allocation': {'lease_repo': str(fixture.repo),
            'task_bus': {'path': str(fixture.root / 'bus/bin/codex_task_bus.py'), 'sha256': 'a' * 64}}}
        for path in (self.selection.runtime_path, self.selection.manifest_path, self.selection.prepared_path):
            path.write_text('{}', encoding='utf-8')
        self.binding: MachineBinding = {'machine_id': fixture.machine,
            'state_root': str(fixture.root / 'prelaunch-ids'), 'admission_root': str(fixture.root / 'admission')}
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(ids, 'current_machine_id', return_value=fixture.machine))
        stack.enter_context(patch.object(ids, 'default_state_root', return_value=fixture.root / 'prelaunch-ids'))
        stack.enter_context(patch.object(allocator, 'runtime_process_inventory', side_effect=lambda *_: self.inventory))
        stack.enter_context(patch.object(allocator, 'current_screen_absent', side_effect=lambda *_: self.packet))
        reducer_value: object = unrun.validate_allocated_unrun
        if not isinstance(reducer_value, allocator._PrelaunchUnrunAdmissionReducer):
            raise AssertionError('Actual shared unrun reducer unavailable')
        self.reducer = reducer_value
        self.closure = self.reduce()
        self.lock_held = False
        self.lock_calls = 0
        self.reducer_under_lock: list[bool] = []
        original_lock: object = ids._exclusive_file_lock
        if not isinstance(original_lock, LockProvider):
            raise AssertionError('Actual shared machine writer lock unavailable')
        self.original_lock = original_lock

    def reduce(self) -> JsonObject:
        return json_object(self.reducer(self.live, self.freeze, self.close, self.keeper,
            self.release, self.packet, next_state=self.next_state))

    def claim(self, mutation: Callable[[], None] | None = None) -> Path:
        @contextmanager
        def locked(path: Path) -> Iterator[None]:
            with self.original_lock(path):
                self.lock_held = True
                self.lock_calls += 1
                try:
                    if mutation is not None:
                        mutation()
                    yield
                finally:
                    self.lock_held = False

        def reduced(previous: Path, freeze_value: object, close_path: Path, keeper_root: Path,
                release_value: object, bus_value: object, *, next_state: Path) -> JsonObject:
            self.reducer_under_lock.append(self.lock_held)
            return self.reducer(previous, freeze_value, close_path, keeper_root, release_value,
                bus_value, next_state=next_state)

        with patch.object(ids, '_exclusive_file_lock', side_effect=locked), \
                patch.object(unrun, 'validate_allocated_unrun', side_effect=reduced):
            return allocator.claim_machine_admission(self.binding, self.selection, self.args, self.closure)

    def assert_unconsumed(self) -> None:
        root = Path(self.binding['admission_root'])
        self.assertFalse((root / 'machine.json').exists())
        self.assertEqual(list(root.glob('[0-9]*')), [])

    def test_actual_reducer_round_trip_and_intent_are_bound_to_original_writer_lock(self) -> None:
        self.closure = json_object(json.loads(json.dumps(self.closure)))
        record = self.claim()
        self.assertEqual(self.lock_calls, 1)
        self.assertEqual(self.reducer_under_lock, [True])
        intent = json_object(json.loads((record / 'intent.json').read_text(encoding='utf-8')))
        self.assertEqual(object_field(intent, 'closure')['mode'],
            'previous-shared-allocated-unrun-prelaunch-orchestrator-failed')
        self.assertFalse(intent['business_pass'])

    def test_host_evidence_appearing_inside_lock_rejects_before_consuming_intent(self) -> None:
        def mutate() -> None:
            (self.live / 'host-started.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'actual host/native/control/Save evidence'):
            self.claim(mutate)
        self.assertEqual(self.reducer_under_lock, [True])
        self.assert_unconsumed()

    def test_current_process_and_screen_observations_are_refreshed_inside_lock(self) -> None:
        for observation in ('process', 'screen'):
            with self.subTest(observation=observation):
                def mutate() -> None:
                    if observation == 'process':
                        self.inventory = {'blockers': [{'pid': 123, 'name': 'ck3.exe'}]}
                    else:
                        self.packet = {'tasks': []}
                with self.assertRaises(ValueError):
                    self.claim(mutate)
                self.assert_unconsumed()
                self.inventory = {'blockers': []}
                self.packet = {'tasks': [{**object_field(self.release, 'task'), 'age_seconds': 0, 'stale': False}]}
        self.assertEqual(self.reducer_under_lock, [True, True])

    def test_closure_pin_change_inside_lock_rejects_before_any_intent(self) -> None:
        def mutate() -> None:
            self.close.write_bytes(self.close.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'closure changed before original writer lock'):
            self.claim(mutate)
        self.assertEqual(self.reducer_under_lock, [])
        self.assert_unconsumed()

    def test_consumed_predecessor_state_cannot_be_reused(self) -> None:
        self.selection.state_dir = Path(text_field(self.freeze, 'state_dir'))
        with self.assertRaisesRegex(ValueError, 'separate next state'):
            self.claim()
        self.assert_unconsumed()


if __name__ == '__main__':
    unittest.main()
