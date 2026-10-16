"""One main-level regression: UTC-day collision, local dedup, next local 04:00."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = (Path(sys.argv.pop(1)) if len(sys.argv) > 1 and sys.argv[1].endswith('.py')
          else Path(__file__).with_name('storage_retention_inspect.py')).resolve()
spec = importlib.util.spec_from_file_location('storage_retention_daily_subject', SOURCE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
SHANGHAI = timezone(timedelta(hours=8))


class LocalClock(datetime):
    current = datetime(2026, 10, 16, 20, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(cls.current.timestamp(), tz)

    def astimezone(self, tz=None):
        return super().astimezone(SHANGHAI if tz is None else tz)


class DailyLocalCalendarRegression(unittest.TestCase):
    def test_first_local_0400_not_suppressed_by_install_utc_day(self):
        # Only a new temporary fixture below this external candidate lane is mutated.
        parent = Path(__file__).resolve().parent / 'fixture-work'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(parent.resolve()))
            (root / 'docs').mkdir()
            policy = root / 'docs/storage-retention-policy.json'
            policy.write_text(json.dumps({'execution': {'inventory_report_max_bytes': 1048576}}), encoding='utf-8')
            profile, ledger = root / 'profile.json', root / 'ledger.json'
            profile.write_text('{}', encoding='utf-8')
            ledger.write_text('{}', encoding='utf-8')
            output = root / 'reports'
            output.mkdir()
            state_file = output / 'daily-state.json'
            state_file.write_text(json.dumps({'machine_id': 'fixture-machine', 'last_daily_date_utc': '2026-10-16', 'last_daily_report': 'installation-report'}), encoding='utf-8')
            args = ['--profile', str(profile), '--ledger', str(ledger), '--output-dir', str(output), '--trigger', 'daily']

            def readonly_result(profile, ledger, policy, machine, observed):
                return {'machine_id': machine, 'observed_at_utc': observed.isoformat(), 'counts': {}, 'deletions': 0, 'automatic_gc_deployed_by_this_tool': False}

            with patch.object(subject, 'REPO', root), patch.object(subject, 'datetime', LocalClock), patch.object(subject.subprocess, 'run', return_value=SimpleNamespace(stdout='fixture-machine\n')), patch.object(subject, 'inspect', side_effect=readonly_result) as inspector, redirect_stdout(io.StringIO()):
                LocalClock.current = datetime(2026, 10, 16, 20, tzinfo=timezone.utc)
                self.assertEqual(subject.main(args), 0)
                self.assertEqual(inspector.call_count, 1, 'Local Oct17 04:00 must create a report despite the installation UTC-day key')
                state = json.loads(state_file.read_text(encoding='utf-8'))
                self.assertEqual(state['last_daily_date_local'], '2026-10-17')
                self.assertEqual(state['last_daily_utc_offset'], '+0800')
                report = json.loads(Path(state['last_daily_report']).read_text(encoding='utf-8'))
                self.assertEqual(report['observed_at_utc'], '2026-10-16T20:00:00+00:00')
                self.assertEqual(report['deletions'], 0)
                self.assertFalse(report['automatic_gc_deployed_by_this_tool'])
                LocalClock.current = datetime(2026, 10, 17, 2, tzinfo=timezone.utc)
                self.assertEqual(subject.main(args), 0)
                self.assertEqual(inspector.call_count, 1, 'Same local day is idempotent even across UTC midnight')
                LocalClock.current = datetime(2026, 10, 17, 20, tzinfo=timezone.utc)
                self.assertEqual(subject.main(args), 0)
                self.assertEqual(inspector.call_count, 2, 'Next local 04:00 creates a fresh report')
                self.assertEqual(len(list(output.glob('*-daily.json'))), 2)
                self.assertEqual(json.loads(state_file.read_text(encoding='utf-8'))['last_daily_date_local'], '2026-10-18')


if __name__ == '__main__':
    unittest.main()
