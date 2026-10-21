"""Exercise only the two real W-growth guards, stopping before Git mutation."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from execution import publish_exact_once_2m_a01 as pub


class ReachedBoundary(RuntimeError):
    pass


class SizedFixture(pub.Pin):
    def read(self) -> bytes:
        # Only the size budget is under test; never materialize multi-MiB data.
        return b'x'


class Probe(pub.Executor):
    def __init__(self, root: Path, size: int, post_copy: bool) -> None:
        cap = Mock(spec=pub.Admission)
        cap.worktree = root
        cap.droot = root
        cap.machine = 'fixture-machine'
        source = SizedFixture(root / 'source', size, pub.sha(b'x'))
        items = () if post_copy else (pub.Item(source, 'new.bin', pub.blob(b'x'), None),)
        pin = pub.Pin(root / 'pin', 0, pub.sha(b''))
        plan = pub.Plan(pin, 'fixture-machine', root, 'a' * 40, 'b' * 40,
                        datetime(2100, 1, 1, tzinfo=timezone.utc), items, 7)
        super().__init__(cap, plan, root, Path(__file__))
        self.records = Mock(spec=pub.Recorder)
        self.after_copy = post_copy
        self.claims: list[str] = []

    def guard(self) -> None:
        pass

    def command(self, label: str, argv: list[str], payload: bytes | None = None,
                mutation: bool = False) -> bytes:
        if mutation:
            raise ValueError('No mutation command is allowed by this fixture')
        if label == 'machine':
            return b'fixture-machine\n'
        if label == 'head':
            return b'a' * 40 + b'\n'
        if label == 'clean':
            return b''
        raise ValueError('Unexpected command: ' + label)

    def remote(self, expected: str, label: str) -> None:
        pass

    def check_d(self) -> None:
        pass

    def claim_phase(self, phase: str) -> None:
        self.claims.append(phase)
        if not self.after_copy or phase == 'stage':
            raise ReachedBoundary(phase)


class GrowthTests(unittest.TestCase):
    def test_prospective_guard_allows_over_old_limit_through_exact_new_limit(self) -> None:
        for count in (1048577, 2097152):
            with self.subTest(bytes=count), tempfile.TemporaryDirectory(dir=ROOT / 'source-checks/tmp') as temp:
                probe = Probe(Path(temp), count, False)
                with patch.object(pub, 'census', return_value=0):
                    with self.assertRaisesRegex(ReachedBoundary, 'copy'):
                        probe.run()
                self.assertEqual(probe.claims, ['copy'])

    def test_prospective_guard_rejects_one_byte_over_before_copy_claim(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / 'source-checks/tmp') as temp:
            probe = Probe(Path(temp), 2097153, False)
            with patch.object(pub, 'census', return_value=0):
                with self.assertRaisesRegex(ValueError, 'prospective W growth'):
                    probe.run()
            self.assertEqual(probe.claims, [])

    def test_actual_guard_allows_exact_new_limit_before_stage(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / 'source-checks/tmp') as temp:
            probe = Probe(Path(temp), 0, True)
            with patch.object(pub, 'census', side_effect=[0, 2097152, 0]):
                with self.assertRaisesRegex(ReachedBoundary, 'stage'):
                    probe.run()
            self.assertEqual(probe.claims, ['copy', 'stage'])

    def test_actual_guard_rejects_one_byte_over_before_stage(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / 'source-checks/tmp') as temp:
            probe = Probe(Path(temp), 0, True)
            with patch.object(pub, 'census', side_effect=[0, 2097153]):
                with self.assertRaisesRegex(ValueError, 'actual W growth'):
                    probe.run()
            self.assertEqual(probe.claims, ['copy'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
