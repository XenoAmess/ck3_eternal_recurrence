"""R0001 actual source shapes -> existing failed-live resource consumer.

Relocated files and absent processes are authored regression inputs. The source
excerpt preserves the full originals' pins separately and grants no live PASS.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance_background_types import JsonObject, JsonValue, file_pin, json_object, text_field, strings_field
from test_product_acceptance_purpose import pin


class PreservedNativeOS0Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = json_object(json.loads((Path(__file__).parent / 'fixtures/ck3_R0001_preserved_failure_native_os0.json').read_bytes()))
        self.original_root = text_field(source, 'original_root').replace('\\', '/')
        self.machine = text_field(source, 'machine_id')
        self.source = source
        self.leaves = json_object(self.relocate(source['leaves']))
        self.refs: JsonObject = {}
        original_pins = json_object(source['source_pins'])
        for key, raw in original_pins.items():
            original = file_pin(raw)
            path = Path(str(self.relocate(original['path'])))
            path.parent.mkdir(parents=True, exist_ok=True)
            if key in self.leaves:
                self.refs[key] = self.write(path, self.leaves[key])
            else:
                if not path.exists():
                    path.write_bytes(b'Authored non-game output\n')
                self.refs[key] = json_object(pin(path))
        self.freeze = json_object(self.leaves['frozen_argv'])
        self.ready = json_object(self.leaves['ready_context'])
        self.run_dir = Path(text_field(self.ready, 'run_dir'))
        self.keeper = Path(text_field(self.ready, 'keeper_root'))
        self.ready['prepared_case'], self.ready['frozen_argv'] = self.refs['prepared_case'], self.refs['frozen_argv']
        self.reseal('ready_context', self.ready)
        argv = strings_field(json_object(self.leaves['run_wait']), 'argv')
        self.write(Path(argv[argv.index('--run-context') + 1]), self.ready)
        self.report = json_object(self.leaves['native_report'])
        self.release_path = Path(text_field(json_object(self.refs['release']), 'path'))
        self.close = self.root / 'resource-close.json'
        self.bundle: JsonObject = {'schema': 'ck3-mod-acceptance-failed-live-resource-closure-v1',
            'machine_id': self.machine, 'run_id': self.run_dir.name, 'keeper_root': str(self.keeper),
            'closure_kind': 'preserved-failure-native-process-exit-zero',
            'public_wait_format': 'root-observed-command-exit-v1',
            'normal_close_qualified': False, 'typed_normal_exit_proven': False,
            'business_pass': False, 'release_pass': False, 'original_evidence': self.refs}
        self.write(self.close, self.bundle)
        # These processes are authored absent fixtures. The actual R0001 test
        # execution is a separate read-only call against the retained originals.
        self.psutil = SimpleNamespace(pid_exists=lambda pid: False, process_iter=lambda fields: [],
            Process=self.missing_process, NoSuchProcess=ProcessAbsent)

    @staticmethod
    def missing_process(pid: int) -> object:
        raise ProcessAbsent()

    def relocate(self, value: JsonValue) -> JsonValue:
        if isinstance(value, str):
            normalized = value.replace('\\', '/')
            if normalized.startswith(self.original_root):
                return str(self.root / 'external' / normalized[len(self.original_root):].lstrip('/'))
            return normalized
        if isinstance(value, list):
            return [self.relocate(item) for item in value]
        if isinstance(value, dict):
            return {key: self.relocate(item) for key, item in value.items()}
        return value

    def write(self, path: Path, value: object) -> JsonObject:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return json_object(pin(path))

    def reseal(self, key: str, value: JsonValue) -> None:
        self.leaves[key] = value
        self.refs[key] = self.write(Path(text_field(json_object(self.refs[key]), 'path')), value)
        if hasattr(self, 'bundle'):
            self.write(self.close, self.bundle)

    def check(self) -> JsonObject:
        release = json_object(self.leaves['release'])
        with patch.dict(sys.modules, {'psutil': self.psutil}), patch.object(allocation,
                'runtime_process_inventory', return_value={'blockers': []}):
            return json_object(allocation.previous_failed_live_resource_closure(self.run_dir,
                {key: value for key, value in self.freeze.items()}, self.close,
                self.keeper, self.release_path, {'tasks': [release['task']]}))

    def test_actual_shapes_roundtrip_original_false_close_and_host_one_are_preserved(self) -> None:
        self.assertEqual(self.source, json.loads(json.dumps(self.source)))
        proof = self.check()
        facts = json_object(proof['failure_cleanup'])
        self.assertEqual(facts['original_host_exit_code'], 1)
        self.assertEqual(facts['original_ck3_exit_code'], 0)
        self.assertEqual(facts['win32_birth_filetime'], '134373083942703873')
        self.assertIs(facts['original_normal_close_lifecycle_completed'], False)
        self.assertIs(facts['failure_lifecycle_completed'], True)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(facts[key], False)
        self.assertIs(json_object(self.leaves['normal_close'])['failure_lifecycle_completed'], False)

    def test_uncompleted_wrong_or_duplicate_finish_and_job_termination_refuse(self) -> None:
        baseline = copy.deepcopy(self.report)
        steps = baseline['steps']
        if not isinstance(steps, list):
            raise ValueError('Actual finish steps required')
        for kind in ('not_ok', 'duplicate', 'missing', 'job_termination'):
            report = copy.deepcopy(baseline)
            row = json_object(copy.deepcopy(steps[0]))
            if kind == 'not_ok':
                row['ok'] = False
                report['steps'] = [row]
            elif kind == 'duplicate':
                report['steps'] = [row, row]
            elif kind == 'missing':
                report['steps'] = []
            else:
                session = json_object(report['session'])
                native = json_object(session['report'])
                shutdown = json_object(native['shutdown'])
                shutdown['job_active_processes_before_termination'] = 1
                native['shutdown'], session['report'], report['session'] = shutdown, native, session
            self.reseal('native_report', report)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.check()

    def test_root_exit_wrong_machine_bool_float_and_filetime_number_refuse(self) -> None:
        baseline = copy.deepcopy(json_object(self.leaves['run_wait']))
        for value in (True, 2.0, 0):
            changed = copy.deepcopy(baseline)
            changed['exit_code'] = value
            self.reseal('run_wait', changed)
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check()
        self.reseal('run_wait', baseline)
        window = json_object(self.leaves['root_window_start'])
        window['birth_filetime'] = 134373083942703873
        self.reseal('root_window_start', window)
        with self.assertRaises(ValueError):
            self.check()


class ProcessAbsent(Exception):
    pass


if __name__ == '__main__':
    unittest.main()
