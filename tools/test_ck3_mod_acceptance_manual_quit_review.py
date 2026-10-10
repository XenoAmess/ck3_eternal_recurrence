"""Portable contract tests; synthetic evidence, never an old/live response."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ck3_mod_acceptance_manual_quit_review as candidate


class ManualQuitReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.live = Path(self.temporary.name) / 'synthetic-R0048'
        self.output = self.live / 'case-output'
        self.output.mkdir(parents=True)
        self.request = self.output / 'normal-quit-awaiting.json'
        self.image = self.live / 'unchecked.png'
        self.after = self.live / 'after.png'
        self.final = self.live / 'after.png.json'
        Image.new('RGB', (8, 6), (120, 130, 140)).save(self.image)
        Image.new('RGB', (8, 6), (140, 130, 120)).save(self.after)
        self.identity = {'run_id': self.live.name, 'live': str(self.live), 'reviewer': '/root',
            'pid': 1832, 'create_time': 1791614801.4849763, 'original_hold_deadline': 2000.0}
        # The real R47 canonical mapper fields, without using/copying its images.
        self.mapping = {'action': 'click', 'click_completed': True, 'failures': [],
            'expected_foreground_hwnd': 721400, 'focus_before': {'foreground_pid': 1832, 'foreground_hwnd': 721400},
            'source_image': str(self.image), 'source_image_size': [8, 6], 'receipt_path': str(self.after)}
        self.save()

    def save(self):
        self.request.write_text(json.dumps(self.identity), encoding='utf-8')
        self.final.write_text(json.dumps(self.mapping), encoding='utf-8')

    def build(self, **kwargs):
        return candidate.build_review(self.request, self.image, self.final, '/root',
            direct_reviewed=kwargs.pop('direct_reviewed', True), now=kwargs.pop('now', 1999.0), **kwargs)

    def test_existing_public_mapped_validator_accepts_response_without_client_startup(self):
        from ck3_mod_acceptance_client import CaseClient
        review, target = self.build()
        view = types.SimpleNamespace(frozen={'run_id': self.live.name},
            _process={'pid': self.identity['pid'], 'create_time': self.identity['create_time']},
            _hold=self.identity['original_hold_deadline'], normal_quit_reviewer=lambda: '/root')
        self.assertIs(CaseClient.validate_manual_normal_quit_review(view, review, require_mapped=True), review)
        self.assertEqual(target, self.output / 'normal-quit-root-result.json')
        self.assertFalse(review['actual_os0_proven'])
        self.assertFalse(review['process_exit_claimed'])

    def test_wrong_foreground_pid_and_wrong_source_are_rejected(self):
        self.mapping['focus_before']['foreground_pid'] += 1
        self.save()
        with self.assertRaisesRegex(ValueError, 'foreground identity'):
            self.build()
        self.mapping['focus_before']['foreground_pid'] -= 1
        self.mapping['source_image'] = str(self.after)
        self.save()
        with self.assertRaisesRegex(ValueError, 'unchecked screenshot'):
            self.build()

    def test_failed_click_or_unreviewed_operator_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'directly review'):
            self.build(direct_reviewed=False)
        self.mapping['click_completed'] = False
        self.save()
        with self.assertRaisesRegex(ValueError, 'did not complete'):
            self.build()

    def test_expired_original_deadline_and_deadline_reached_during_validation_do_not_write(self):
        with self.assertRaisesRegex(ValueError, 'deadline expired'):
            self.build(now=2000.0)
        times = iter([1999.0, 2000.0])
        with self.assertRaisesRegex(ValueError, 'deadline expired'):
            candidate.write_review(self.request, self.image, self.final, '/root',
                direct_reviewed=True, clock=lambda: next(times))
        self.assertFalse((self.output / 'normal-quit-root-result.json').exists())

    def test_canonical_response_is_create_only(self):
        ref = candidate.write_review(self.request, self.image, self.final, '/root', direct_reviewed=True, clock=lambda: 1999.0)
        original = Path(ref['path']).read_bytes()
        with self.assertRaises(FileExistsError):
            candidate.write_review(self.request, self.image, self.final, '/root', direct_reviewed=True, clock=lambda: 1999.0)
        self.assertEqual(Path(ref['path']).read_bytes(), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
