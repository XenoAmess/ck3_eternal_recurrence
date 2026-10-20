"""Python routing tests only. Never execute either native fixture target."""
from pathlib import Path
from contextlib import redirect_stderr
from datetime import datetime, timezone
import argparse, ctypes, hashlib, importlib.util, io, json, subprocess, sys, tempfile, unittest
from unittest.mock import patch, Mock

EXPECTED_DEFAULT = ('four-writes', 'same-value', 'new-worker', 'timeout',
                    'changed-context', 'default-off', 'unaligned', 'wrong-fullid')
SELECTED = ['four-writes', 'timeout', 'default-off', 'ordinary-ownership-rejection']
FORBIDDEN = AssertionError('This test must not call native/OS execution')
HERE = Path(__file__).resolve().parent

def load_runner(path):
    spec = importlib.util.spec_from_file_location('_writer_cold_selection_under_test', path)
    module = importlib.util.module_from_spec(spec)
    with patch.object(ctypes, 'WinDLL', side_effect=FORBIDDEN, create=True), \
         patch.object(subprocess, 'Popen', side_effect=FORBIDDEN), \
         patch.object(subprocess, 'check_output', side_effect=FORBIDDEN):
        spec.loader.exec_module(module)
    return module

class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner(cls.source)

    def argv(self, output):
        return ['--repo', str(HERE), '--build-dir', str(HERE/'UNUSED-BUILD'),
                '--machine-build-record', str(HERE/'UNREAD-BUILD.json'),
                '--output-root', str(output)]

    def test_default_retains_original_eight_in_order(self):
        options = self.runner.make_parser().parse_args(self.argv(HERE/'UNUSED-OUT'))
        self.assertIsNone(options.case)
        self.assertEqual(self.runner.select_cases(options.case), EXPECTED_DEFAULT)
        self.assertNotIn('ordinary-ownership-rejection', EXPECTED_DEFAULT)

    def test_real_main_dispatches_only_selected_four_after_gate(self):
        events = []
        with tempfile.TemporaryDirectory(dir=HERE,prefix='selection-route-') as scratch:
            root = Path(scratch)/'out'
            def initialize(options):
                events.append('initialize')
                self.runner.OUT = options.output_root
                self.runner.MACHINE = 'synthetic-routing-only'
            def gate(*,require_ordinary_source):
                events.append(('gate',require_ordinary_source))
                return {'classification': 'mock-routing-not-SYSTEM'}
            def run_case(mode):
                events.append(mode)
                return {'mock_routing_case': mode, 'native_executed': False}
            # No fake suite is published: writes are intercepted in memory.
            with patch.object(self.runner,'initialize',side_effect=initialize), \
                 patch.object(self.runner,'gate',side_effect=gate), \
                 patch.object(self.runner,'run_case',side_effect=run_case) as case_mock, \
                 patch.object(self.runner,'write') as writes, \
                 patch.object(subprocess,'Popen',side_effect=FORBIDDEN), \
                 patch.object(ctypes,'WinDLL',side_effect=FORBIDDEN,create=True):
                argv=self.argv(root)
                for mode in SELECTED:argv += ['--case',mode]
                self.assertEqual(self.runner.main(argv),0)
                self.assertEqual(events,['initialize',('gate',True)]+SELECTED)
                self.assertEqual(case_mock.call_count,4)
                self.assertEqual(len(writes.call_args_list),2)
                suite=writes.call_args_list[-1].args[1]
                self.assertEqual(suite['case_count'],4)
                self.assertEqual(suite['selected_cases'],SELECTED)
                self.assertFalse(suite['default_eight_cases'])
                self.assertFalse(suite['ordinary_native_owner_accepted'])
                self.assertFalse(suite['CK3_observed'])
                self.assertEqual(list(root.iterdir()),[])

    def test_failed_system_gate_never_dispatches_case_or_success_suite(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='selection-gate-') as scratch:
            def initialize(options):
                self.runner.OUT=options.output_root
            with patch.object(self.runner,'initialize',side_effect=initialize), \
                 patch.object(self.runner,'gate',side_effect=RuntimeError('synthetic gate refused')), \
                 patch.object(self.runner,'run_case') as run_case, \
                 patch.object(self.runner,'write') as writes:
                with self.assertRaisesRegex(RuntimeError,'gate refused'):
                    self.runner.main(self.argv(Path(scratch)/'out')+['--case','four-writes'])
                run_case.assert_not_called()
                writes.assert_not_called()

    def test_duplicate_unknown_and_empty_selection_reject_before_initialization(self):
        variants=[['--case','four-writes','--case','four-writes'], ['--case','not-a-case']]
        with patch.object(self.runner,'initialize') as initialize, redirect_stderr(io.StringIO()):
            for tail in variants:
                with self.subTest(tail=tail), self.assertRaises(SystemExit) as caught:
                    self.runner.main(self.argv(HERE/'UNUSED-OUT')+tail)
                self.assertEqual(caught.exception.code,2)
            initialize.assert_not_called()
        with self.assertRaisesRegex(ValueError,'at least one'):
            self.runner.select_cases([])

    def test_ordinary_negative_uses_existing_zero_write_target_and_exact_native_option(self):
        self.runner.BUILD=HERE/'UNUSED-BUILD'
        self.runner.MACHINE='synthetic-routing-only'
        mode='ordinary-ownership-rejection'
        argv=self.runner.make_observer_argv(mode,HERE/'UNREAD.meta.txt',HERE/'UNCREATED.raw',HERE/'UNCREATED.ready')
        self.assertEqual(self.runner.target_mode(mode),'default-off')
        self.assertEqual(len(argv),15)
        self.assertEqual(argv[1:3],['--enable-cold-fixture','--fixture-meta'])
        self.assertEqual(argv[-1],'--ordinary-null-owner-binding')
        self.assertEqual(argv[4:6],['--timeout-ms','5000'])
        self.assertNotIn('--enable-ck3-12004-data-watch',argv)
        self.assertNotIn('--capture-known-copy-caller',argv)

    def test_existing_native_argv_shapes_remain_default_off_and_four_slots(self):
        self.runner.BUILD=HERE/'UNUSED-BUILD'
        self.runner.MACHINE='synthetic-routing-only'
        for mode in EXPECTED_DEFAULT:
            with self.subTest(mode=mode):
                argv=self.runner.make_observer_argv(mode,'meta','raw','ready')
                self.assertEqual(self.runner.target_mode(mode),mode)
                self.assertEqual(len(argv),1 if mode=='default-off' else 14)
                if mode!='default-off':
                    self.assertEqual(argv[10:12],['--expected-hits','4'])
                    self.assertEqual(argv[5],'1000' if mode=='timeout' else '5000')
                    self.assertEqual(argv[1],'--enable-cold-fixture')

    def test_required_original_build_and_output_inputs_are_still_required(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.runner.make_parser().parse_args(['--case','four-writes'])
        self.assertEqual(caught.exception.code,2)

    def test_ordinary_cell_rejects_old_system_source_pin_even_if_old_exe_would_exit2(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='ordinary-source-') as scratch:
            self.runner.REPO=Path(scratch)
            source=Path(scratch)/'ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/cold_observer.cpp'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'current maintained ordinary-null observer source')
            for pins in [[],[{'path':'old/cold_observer.cpp','sha256':'24b9d584ee451ef822c6386484efcda2578072cb5569ce1740b910e3bbadd0ee'}]]:
                with self.subTest(pins=pins), self.assertRaisesRegex(RuntimeError,'a07 is incompatible'):
                    self.runner.require_current_ordinary_source({'input_pins':pins})
            self.runner.require_current_ordinary_source({'input_pins':[{
                'path':'frozen/cold_observer.cpp','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE/'run_cold_fixture.py')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--machine-id',default='unknown',help='Execution label; independently read by the caller, not a native qualification')
    options=parser.parse_args()
    SelectionTests.source=options.source.resolve()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelectionTests))
    if options.output:
        report=dict(schema='xar.maintenance.writer_pc.cold-selection-python-check.v1',
            machine_id=options.machine_id,observed_at_utc=datetime.now(timezone.utc).isoformat(),
            classification='PYTHON_ROUTING_ONLY_NO_NATIVE_EXECUTION',
            source=dict(path=str(SelectionTests.source),bytes=SelectionTests.source.stat().st_size,
                        sha256=hashlib.sha256(SelectionTests.source.read_bytes()).hexdigest()),
            test_count=result.testsRun,successful=result.wasSuccessful(),
            failure_count=len(result.failures),error_count=len(result.errors),
            project_EXEs_executed=0,SYSTEM_qualifications_granted=0,CK3_observed=False,
            ordinary_native_memory_path_qualified=False,native_cold_suite_written=False)
        with options.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
