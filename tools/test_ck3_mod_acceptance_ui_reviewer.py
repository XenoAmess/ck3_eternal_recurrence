"""Portable reviewer seam tests; temporary mailbox bytes only, no desktop or CK3."""
from pathlib import Path
from types import SimpleNamespace
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = load(HERE / 'ck3_mod_acceptance_cases/xqol_ui.py', 'reviewer_test_controller')
mailbox = load(HERE / 'ck3_mod_acceptance_ui_mailbox.py', 'reviewer_test_mailbox')
DELEGATE = '/root/ccc_resume_inputs'


def fixture(root, *, reviewer=None):
    ui = root / 'ui25'
    (ui / 'requests').mkdir(parents=True)
    image = root / 'original-fixture.png'
    image.write_bytes(b'only-file-pin-test-fixture-no-pixels-interpreted')
    raw = image.read_bytes()
    source = {'path': str(image), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    awaiting = {'sequence': 0, 'run_id': 'test-R0001', 'stage': 'civic-candidates',
                'original_png': source, 'deadline': 2**40, 'remaining_seconds': 900,
                'request_path': str(ui / 'requests/request-0000.json'), 'actions': ['typed']}
    if reviewer is not None:
        awaiting['operator_reviewer'] = reviewer
    (ui / 'await-0000.json').write_text(json.dumps(awaiting), encoding='utf-8')
    payload = root / 'payload.json'
    payload.write_text(json.dumps({'typed_action': 'snapshot', 'arguments': {}}), encoding='utf-8')
    return ui, source, payload


class ReviewerSeam(unittest.TestCase):
    def test_client_property_default_and_actual_delegate(self):
        self.assertEqual(controller._operator_reviewer(SimpleNamespace()), '/root')
        self.assertEqual(controller._operator_reviewer(SimpleNamespace(operator_reviewer=DELEGATE)), DELEGATE)
        for invalid in (None, '', ' ', False):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                controller._operator_reviewer(SimpleNamespace(operator_reviewer=invalid))

    def test_controller_publish_and_source_guard_use_same_identity(self):
        for reviewer in ('/root', DELEGATE):
            with self.subTest(reviewer=reviewer), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                ui, source, _ = fixture(root)
                (ui / 'await-0000.json').unlink()
                value = object.__new__(controller.Controller)
                value.operator_reviewer = controller._operator_reviewer(SimpleNamespace(operator_reviewer=reviewer))
                value.out = ui
                value.live = root / 'test-R0001'
                value.seq = value.stage = 0
                value.deadline = 2**40
                value.remaining = lambda: 900
                value.capture = lambda name: source
                value.latest = source
                calls = []
                value.guard = lambda: calls.append('actual-guard')
                with contextlib.redirect_stdout(io.StringIO()):
                    value.publish()
                awaiting = json.loads((ui / 'await-0000.json').read_bytes())
                self.assertEqual(awaiting['operator_reviewer'], reviewer)
                self.assertEqual(awaiting['sequence'], 0)
                self.assertEqual(awaiting['deadline'], 2**40)
                request = {'reviewer': reviewer, 'run_id': value.live.name, 'sequence': 0, 'source': source}
                value.source_guard(request)
                self.assertEqual(calls, ['actual-guard'])
                with self.assertRaises(RuntimeError):
                    value.source_guard({**request, 'reviewer': '/root/wrong-operator'})
                self.assertEqual(calls, ['actual-guard'])

    def test_mailbox_old_default_and_delegate_envelope(self):
        for expected, supplied in ((None, None), ('/root', '/root'), (DELEGATE, DELEGATE)):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                ui, source, payload = fixture(root, reviewer=expected)
                args = SimpleNamespace(ui_dir=ui, sequence=0, action='typed', payload_file=payload,
                                       reviewed_sha256=source['sha256'])
                if supplied is not None:
                    args.reviewer = supplied
                result = mailbox.submit(args)
                envelope = json.loads(Path(result['request_path']).read_bytes())
                actual = expected or '/root'
                self.assertEqual(envelope['reviewer'], actual)
                self.assertEqual(result['reviewer'], actual)
                self.assertEqual(envelope['source'], source)
                self.assertFalse(result['input_executed_by_helper'])
                self.assertFalse(result['business_pass_inferred'])
                before = Path(result['request_path']).read_bytes()
                with self.assertRaises(ValueError):
                    mailbox.submit(args)
                self.assertEqual(Path(result['request_path']).read_bytes(), before)

    def test_mailbox_wrong_identity_rejected_without_request(self):
        for expected, supplied in ((DELEGATE, '/root'), ('/root', DELEGATE), (DELEGATE, '/root/other')):
            with self.subTest(expected=expected, supplied=supplied), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                ui, source, payload = fixture(root, reviewer=expected)
                args = SimpleNamespace(ui_dir=ui, sequence=0, action='typed', payload_file=payload,
                                       reviewed_sha256=source['sha256'], reviewer=supplied)
                with self.assertRaises(ValueError):
                    mailbox.submit(args)
                self.assertFalse((ui / 'requests/request-0000.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
