"""Two new offline title-reference tests; no existing provider tests are rerun."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import sys
import tempfile
import types
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--support-repo', type=Path, default=Path(__file__).resolve().parents[1])
parser.add_argument('--fixture-repo', type=Path)
options, remaining = parser.parse_known_args()
MAIN = options.support_repo
REPO = options.fixture_repo or Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/'tools'))
sys.path.insert(0, str(MAIN/'tools'))
import ck3_mod_acceptance_appointment as appointment
import ck3_mod_acceptance_client as clientmod
# Reuse unchanged synthetic wire builders only; none of their tests is run.
from test_ck3_mod_acceptance_appointment import frame, row

TITLE = 14770  # Explicit offline synthetic fixture identity, never a live ID.
KEY = 'e_minister_grand_marshal'
LAW = 'celestial_grand_marshal_appointment_succession_law'


def reference():
    holder = dict(schema='xar.ck3.title-holder.v1', schema_version=1, available=True, status='available',
                  title_id=TITLE, title_key_available=True, title_key_status='available', title_key=KEY,
                  holder_character_id=201, actor_character_id=101, date_raw=8000,
                  snapshot_revision=9, game_version='1.20.0.4', executable_sha256=appointment.EXE_SHA)
    return dict(id='offline-native-title-reference', ok=True, error=None, finished_at='offline-only',
                plan=dict(tool='ck3_query_title_holder_v1', args=dict(title_id=TITLE), fresh_revision=True),
                result=dict(accepted=True, status='available', step='query-title-holder-v1-'+str(TITLE),
                            read_only=True, title_id=TITLE, queried_native_revision=9, title_holder=holder),
                after_snapshot=frame())


def client(output, ref):
    c = object.__new__(clientmod.CaseClient)
    c.output = output
    c._seq = 0
    c.frozen = dict(run_id='offline-test-only')
    c.selection = types.SimpleNamespace(case=dict(id='ui_tail', required_mcp_tools=[appointment.TOOL],
                                                  opt_in_read_only_mcp_tools=[appointment.TOOL]))
    c._process = dict(pid=1001, create_time=123.0, retained_synchronize_query_handle_acquired=True)
    c.guard = lambda *a, **k: None
    c.snapshot = frame
    c.validate_frame = lambda f: f
    c.read_report = lambda: dict(steps=[ref])

    def execute(steps, name):
        step = steps[0]
        if step['tool'] == 'ck3_query_title_holder_v1':
            return [reference()]
        actual = row()
        actual['id'] = step['id']
        v = actual['result']['title_appointment']
        v.update(current_window_title_id=TITLE, resolved_title_id=TITLE, group_first_title_id=TITLE,
                 current_title_key=KEY, resolved_title_key=KEY, effective_succession_law_key=LAW)
        actual['result']['current_subject_id'] = TITLE
        return [actual]

    c.execute_plan = execute
    return c


class NativeTitleReference(unittest.TestCase):
    def test_successful_current_title_reference_is_collected_without_navigation(self):
        ref = reference()
        actual = appointment.title_reference(ref, frame(), TITLE, KEY)
        self.assertFalse(actual['navigation_claimed'])
        args = dict(requested_title_id=TITLE, requested_title_key=KEY, expected_law=LAW,
                    title_reference_step_id=ref['id'], breakdown_character_id=101)
        self.assertEqual(appointment.collection_arguments(args), args)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            c = client(output, ref)
            path = MAIN/'tools/ck3_mod_acceptance_cases/xqol_ui.py'
            spec = importlib.util.spec_from_file_location('candidate_ui_reference', path)
            ui = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ui)
            controller = object.__new__(ui.Controller)
            controller.client = c
            controller.out = output/'ui'
            controller.out.mkdir()
            collected = controller.typed('appointment-full-pool', args, 'offline-reference')
            proof = collected['proof']
            self.assertEqual(proof['title_reference'], actual)
            self.assertNotIn('navigation', proof)
            self.assertEqual(proof['requested_holder_character_id'], actual['holder_character_id'])
            self.assertEqual(len(proof['candidates']), 2)
            self.assertEqual(c.appointment_receipt(collected['appointment_pool'], frame()), proof)
            # The same admitted key reaches the existing government checkpoint.
            gov = object.__new__(clientmod.CaseClient)
            gov.output = output/'government'
            gov.output.mkdir()
            gov.frozen = c.frozen
            gov.operator_reviewer = '/offline-test-only/operator'
            gov._hold = 220
            gov.remaining = lambda: 200
            gov.guard = lambda *a, **k: None
            gov.selection = types.SimpleNamespace(case=dict(id='administrative_appointments',
                          opt_in_read_only_mcp_tools=[appointment.TOOL]))
            request = dict(action='appointment-full-pool', run_id=gov.frozen['run_id'],
                           reviewer=gov.operator_reviewer, sequence=0, arguments=args)
            (gov.output/'ref-readonly-request-0000.json').write_text(json.dumps(request), encoding='utf-8')
            (gov.output/'ref-root-result.json').write_text(json.dumps(dict(run_id=gov.frozen['run_id'],
                                                                         reviewer=gov.operator_reviewer)), encoding='utf-8')
            calls = []
            gov.query_appointment_pool = lambda **kw: calls.append(kw) or dict(business_acceptance='NOT_ASSESSED')
            gov.root_checkpoint('ref', {}, read_only_appointment=True)
            self.assertEqual(calls, [args])
            meta = json.loads((gov.output/'ref-awaiting.json').read_bytes())['read_only_action']
            self.assertEqual(meta['exactly_one_reference'], ['navigation_step_id','title_reference_step_id'])

    def test_failed_center_or_mismatched_native_reference_cannot_be_consumed(self):
        ref = reference()
        mutations = [
            (('ok',), False),
            (('result','accepted'), False),
            (('result','title_holder','title_id'), TITLE+1),
            (('result','title_holder','title_key'), 'd_zhexi'),
            (('result','title_holder','holder_character_id'), None),
            (('result','title_holder','snapshot_revision'), 8),
            (('after_snapshot','diagnostics','bridge_pid'), 1002),
            (('plan','tool'), 'ck3_center_map_on_landed_title_v1'),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                changed = copy.deepcopy(ref)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    appointment.title_reference(changed, frame(), TITLE, KEY)
        args = dict(requested_title_id=TITLE, requested_title_key=KEY, expected_law=LAW,
                    title_reference_step_id=ref['id'], navigation_step_id='offline-failed-center')
        with self.assertRaises(ValueError):
            appointment.collection_arguments(args)
        with tempfile.TemporaryDirectory() as tmp:
            mismatched = copy.deepcopy(ref)
            mismatched['result']['title_holder']['holder_character_id'] = 202
            c = client(Path(tmp), mismatched)
            with self.assertRaisesRegex(ValueError, 'native normalization holder'):
                c.query_appointment_pool(requested_title_id=TITLE, requested_title_key=KEY, expected_law=LAW,
                                         title_reference_step_id=ref['id'], breakdown_character_id=101)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
