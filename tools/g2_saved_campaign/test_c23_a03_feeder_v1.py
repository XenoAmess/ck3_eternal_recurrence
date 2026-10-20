"""Focused RAM-only A03 inverse, HOLD and DTO-v2 consumer qualification.

Execute the original selected MCP/Queue/feeder algorithms with local objects.
No server, transport, Task, Game or runtime writer is started.
"""
import argparse
import ast
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import types
import unittest

import prepare_c23_a03_feeder_v1 as source

OWN = Path(__file__).resolve().parent
SDK = source.T.parents[1] / 'sdk-v20261019-candidate/src19/xar_autoplayer/bridge'
CANDIDATE = OWN / 'candidates/exact_clock_wait_progress_20261020'
READ_REFS = []
DETAILS = {}
DEADLINE = None
CONSUMER_PINS = {
    'mcp_server.py': (264620, '75e01e9b117fd6a64de10b7971a65a0571ffe3923e93aa7065f166987ab05de5'),
    'driver.py': (20571, '571c3776ac958d38d15906412f7f7af24cc6be098d62341a479ec905f48a9c31'),
    'domain_construction_private_transport_v1.py': (66026, 'c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e'),
    'exact_clock_failure_diagnostic_v1.py': (6624, '8bf4dc3413fae7634999e3bd1b3509c2b9f2b9a58e0a13ee1abb7a477c52276f'),
}


def read_input(path, pin):
    raw = source.read_source(path, pin)
    READ_REFS.append(source.ref(path, raw))
    return raw


def selected(raw, names, env, *, nested=False):
    tree = ast.parse(raw)
    pool = ast.walk(tree) if nested else tree.body
    nodes = [copy.deepcopy(n) for n in pool
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name in names]
    if {n.name for n in nodes} != set(names) or len(nodes) != len(names):
        raise AssertionError('one exact selected AST required: ' + repr(names))
    for node in nodes:
        node.decorator_list = []  # Local invocation omits server registration only.
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 '<exact selected source algorithms>', 'exec'), env)
    return env


def module(name, raw=None, names=None, env=None):
    value = types.ModuleType(name)
    value.__package__ = name.rpartition('.')[0]
    if env:
        value.__dict__.update(env)
    sys.modules[name] = value
    if raw is not None:
        if names is None:
            exec(compile(raw, '<exact generated module>', 'exec'), value.__dict__)
        else:
            selected(raw, names, value.__dict__)
    return value


def assigned(raw, name):
    found = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(found) != 1:
        raise AssertionError('one literal source constant required: ' + name)
    return ast.literal_eval(found[0])


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph, cls.report = source.build_sources(review_deadline_utc=DEADLINE)
        cls.before = {name: read_input(source.T / name, pin) for name, pin in source.PINS.items()}

    def test_exact_inverse_and_timing_hold_unchanged(self):
        self.assertTrue(self.report['whole_byte_inverse_pass'])
        self.assertEqual(self.report['thin_seams'], 3)
        self.assertLessEqual(sum(map(len, self.graph.values())), 98304)
        self.assertEqual(self.graph[source.LEDGER], self.before[source.LEDGER])
        self.assertEqual(self.graph[source.LAUNCHER], self.before[source.LAUNCHER])
        self.assertNotIn(b'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json', self.graph[source.FEEDER])
        functions = source.function_asts(self.graph[source.FEEDER])
        for name in ('publish_or_follow', 'result_for', 'main', 'c23_first_batch_hold',
                     'c23_gate_expected', 'c23_accept_continue', 'continuity_attach'):
            self.assertEqual(functions[name], source.function_asts(self.before[source.FEEDER])[name])
        old_tool = read_input(OWN / 'prepare_c23_full_enabled_cold_controls_v1.py',
                             (37154, 'b63eacea6eae778678e7a05f755e033bb426e67da8c0cebc5bb465f3199051d9'))
        old_entry = [n for n in ast.parse(old_tool).body if isinstance(n, ast.FunctionDef)
                     and n.name == 'transform_cold_feeder_source']
        self.assertEqual(len(old_entry), 1)
        self.assertEqual(hashlib.sha256(ast.dump(old_entry[0], include_attributes=False).encode()).hexdigest(),
                         'b9d3a1ca97b7d06d5bf4b0648df64f1b63061303ebe59fea96b14ff92890fceb')
        for name, raw in self.before.items():
            with self.subTest(drift=name), self.assertRaises(ValueError):
                source.checked_bytes(raw + b'\n', source.PINS[name], name)

    def test_new_deadline_required(self):
        for value in (source.OLD_DEADLINE, '2026-10-20T06:30:00', 'not-a-date', None,
                      '2026-10-20T08:30:00+02:00'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.validate_deadline(value)
        self.assertEqual(source.validate_deadline(DEADLINE), DEADLINE)

    def test_root_continue_binds_exact_first_batch(self):
        env = selected(self.graph[source.FEEDER], {'c23_require', 'c23_accept_continue'},
                       {'datetime': datetime, 'timezone': timezone})
        now = datetime.now(timezone.utc)
        expected = {'review_deadline_utc': DEADLINE,
                    'hold_started_at_utc': (now - timedelta(seconds=1)).isoformat(),
                    'request': {'sha256': 'a' * 64}, 'feeder_task_nonce': '1' * 32}
        marker = {'schema': 'xar.C23-first-FULL-root-continue/v1', 'reviewer': '/root',
                  'reviewed_at_utc': now.isoformat(), 'first_batch': copy.deepcopy(expected)}
        self.assertTrue(env['c23_accept_continue'](marker, expected))
        for key in ('request', 'feeder_task_nonce'):
            bad = copy.deepcopy(marker)
            bad['first_batch'][key] = 'different'
            with self.subTest(key=key), self.assertRaises(ValueError):
                env['c23_accept_continue'](bad, expected)

    def test_dto_v2_through_original_mcp_queue_and_feeder(self):
        inputs = {name: read_input(SDK / name, pin) for name, pin in CONSUMER_PINS.items()}
        candidate = read_input(CANDIDATE / 'prepare_candidate.py',
                              (8267, 'c21d8acb85d8ba83543c6a8842c48cde74e6e00cd084299cddbd31ff79cb1d67'))
        helper_raw = read_input(CANDIDATE / 'exact_clock_wait_progress_v1.py',
                               (11494, '531fd68c628062672880b3a67418f5e7d75e82796bf09dd13b05a2ce7a895d3f'))
        dto_raw = inputs['exact_clock_failure_diagnostic_v1.py']
        changes = []
        for old, new in assigned(candidate, 'DTO_HUNKS'):
            dto_raw = source.change(dto_raw.decode(), old, new, changes).encode()
        source.inverse(dto_raw, changes, inputs['exact_clock_failure_diagnostic_v1.py'])
        self.assertEqual((len(dto_raw), source.sha(dto_raw)),
                         (6893, '7645e52a2b221a5e9a813f0e243f9f8a2f6e59f9b08f998a15bc70500af16f0e'))
        prefix = '_c23_a03_clock_dto_probe'
        registered_before = set(sys.modules)
        try:
            package = module(prefix)
            package.__path__ = []
            driver = module(prefix + '.driver', inputs['driver.py'],
                            {'BridgeUnavailableError', 'StepPostconditionError'})
            helper = module(prefix + '.exact_clock_wait_progress_v1', helper_raw)
            dto = module(prefix + '.exact_clock_failure_diagnostic_v1', dto_raw)
            construction_raw = inputs['domain_construction_private_transport_v1.py']
            module(prefix + '.domain_construction_private_transport_v1', construction_raw,
                   {'construction_transport_diagnostic'},
                   {'_CONSTRUCTION_DIAGNOSTIC_MARKER': assigned(construction_raw, '_CONSTRUCTION_DIAGNOSTIC_MARKER')})
            progress = helper.WaitProgressV1({}, 1, clock=lambda: 0).freeze({})
            cause = driver.BridgeUnavailableError('original local failure')
            diagnostic = dto.build_exact_clock_failure_v1(original_error=cause,
                starting_date_raw=53274624, target_date_raw=53274648, speed=5,
                arm_status={'generation': 1}, starting={}, last_frame={}, cleanup_before_frame={},
                actions=[], action_start=0, cleanup_start=0, wait_progress=progress)
            typed = driver.StepPostconditionError(dto.MESSAGE, step_result=diagnostic,
                                                  selected_step='life-advance-one-day')
            typed.__cause__ = cause
            self.assertEqual(dto.exact_clock_failure_diagnostic_v1(typed), diagnostic)
            calls = []
            def fail():
                calls.append('local_service_auto_turn')
                raise typed
            mcp_env = {'__package__': prefix, 'BridgeUnavailableError': driver.BridgeUnavailableError,
                       'start_army_timing': lambda *a, **k: None, 'successor_owner': None,
                       'before_auto_turn_submit': None, 'service': types.SimpleNamespace(auto_turn=fail),
                       '_native_command_rejection_diagnostic': lambda error: None}
            selected(inputs['mcp_server.py'], {'ck3_auto_turn'}, mcp_env, nested=True)
            result = mcp_env['ck3_auto_turn']()
            dumped = result.model_dump(mode='json')  # Exact existing Queue.call serialization.
            self.assertEqual(len(calls), 1)
            self.assertIs(typed.__cause__, cause)
            self.assertIs(dumped['is_error'], True)
            projected = dumped['structured_content']['diagnostics']['exact_day_clock_failure_v1']
            self.assertEqual(projected['schema'], 'xar.exact-day-clock-failure.v2')
            self.assertEqual(projected['wait_progress'], progress)
            self.assertEqual(projected['credit'], 0)
            self.assertIs(projected['never_replay'], True)
            queue_raw = read_input(source.T / 'root_p37c23_sdk_queue.py',
                                   (269159, 'f7dddc9485086ef203a2a169161a7245964d54790c641390ca5af3f4411171e3'))
            queue_env = selected(queue_raw, {'decoded'}, {'json': json})
            for wrapper in (dumped, result.model_dump(mode='json', by_alias=True)):
                row = {'result': wrapper}
                frozen_row = copy.deepcopy(row)
                with self.assertRaisesRegex(RuntimeError, 'no automatic retry'):
                    queue_env['decoded'](row)
                self.assertEqual(row, frozen_row)
            request = {'sequence': 10481, 'command': 'full_loop', 'arguments': {'max_turns': 30}}
            inbox, outbox = Path('INBOX'), Path('OUTBOX')
            response = outbox / '10481-1-result.json'
            failed_full = {'request': request, 'client_error': 'SDK error; original result retained',
                           'original_response': 'retained-original', 'replay_allowed': False}
            rows = {inbox / response.name: request, response: failed_full}
            feeder_env = selected(self.graph[source.FEEDER], {'request_path', 'result_for'},
                {'Path': Path, 'OUTBOX': outbox, 'INBOX': inbox, 'request_maximum': lambda _: 30,
                 'read': rows.__getitem__, 'BASELINE_CYCLES': 4753, 'BASELINE_DATE_RAW': 53144328})
            with self.assertRaisesRegex(ValueError, 'not a successful bounded batch'):
                feeder_env['result_for'](10481, first=True, previous_cycles=4753)
            wrong = copy.deepcopy(diagnostic)
            wrong['schema'] = 'xar.exact-day-clock-failure.v1'
            typed.step_result = wrong
            self.assertIsNone(dto.exact_clock_failure_diagnostic_v1(typed))
            typed.step_result = diagnostic
            self.assertIsNone(dto.exact_clock_failure_diagnostic_v1(cause))
            DETAILS['DTO_v2_consumers'] = {
                'generated_DTO': {'bytes': len(dto_raw), 'sha256': source.sha(dto_raw)},
                'generated_helper': {'bytes': len(helper_raw), 'sha256': source.sha(helper_raw)},
                'MCP_actual_CallToolResult_serialization': True,
                'Queue_error_preserved_no_automatic_retry': True,
                'feeder_no_success_or_credit': True, 'typed_cause_identity_preserved': True,
                'mixed_v1_v2_rejected': True, 'old_candidate_five_tests_repeated': False,
            }
        finally:
            for name in list(sys.modules):
                if name not in registered_before and (name == prefix or name.startswith(prefix + '.')):
                    sys.modules.pop(name, None)


def main():
    global DEADLINE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-deadline-utc', required=True)
    args = parser.parse_args()
    DEADLINE = source.validate_deadline(args.review_deadline_utc)
    started = time.monotonic()
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
    report = {'schema': 'xar.C23-A03-thin-feeder-qualification/v1',
              'machine_id': source.MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
              'review_deadline_utc': DEADLINE, 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'duration_seconds': time.monotonic() - started, 'details': DETAILS,
              'source_graph': Qualification.report,
              'consumer_input_refs': READ_REFS,
              'runtime_writes': 0, 'scratch_bytes': 0, 'MCP_server_or_transport_calls': 0,
              'Task_Game_Native_OBS_desktop_calls': 0}
    if not result.wasSuccessful():
        report['test_output'] = output.getvalue()
    print(json.dumps(report, separators=(',', ':')))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
