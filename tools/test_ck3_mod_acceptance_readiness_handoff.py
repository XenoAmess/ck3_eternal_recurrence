"""Offline public-run/readiness handoff; no launcher, native or desktop calls."""
from pathlib import Path
from contextlib import nullcontext
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock, patch
import json
import sys
import tempfile

import ck3_mod_acceptance as entry
import ck3_mod_acceptance_client as client_source
from ck3_mod_acceptance_cases import rmtm_adapter, ted_adapter


class StopAtFirstObservation(Exception):
    """Synthetic boundary: never execute a business query or advance a day."""


class ReadinessHandoff(TestCase):
    def test_public_run_owns_single_readiness_before_original_adapter_entry(self):
        routes = (
            (rmtm_adapter, 'core', 'rmtm-D0-qualified'),
            (rmtm_adapter, 'threshold_ui', 'rmtm-threshold-D0-qualified'),
            (ted_adapter, 'production_ui', 'ted-production-UI-D0-qualified'),
        )
        for adapter, case, prefix in routes:
            with self.subTest(adapter=adapter.__name__, case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection = entry.Selection.__new__(entry.Selection)
                selection.context = {
                    'run_id': 'SYNTHETIC-NO-GAME', 'keeper_root': 'synthetic-keeper',
                    'proof': 'synthetic-proof', 'challenge': 'synthetic-challenge',
                    'observed_nonce': 'synthetic-nonce', 'reviewer': 'synthetic-reviewer',
                    'frozen_argv': {'path': 'synthetic-frozen.json', 'bytes': 1, 'sha256': 'a' * 64},
                }
                selection.context_path = root / 'synthetic-context.json'
                selection.runtime_path = root / 'synthetic-runtime.json'
                selection.runtime = {
                    'reviewed_launcher': {'path': 'NEVER-STARTED.py', 'bytes': 1, 'sha256': 'b' * 64},
                    'manifest': {'path': 'synthetic-manifest.json', 'bytes': 1, 'sha256': 'c' * 64},
                }
                selection.locations = {'python': Path(sys.executable), 'repo_root': root}
                selection.runtime_environment = {}
                selection.run_dir = root / 'SYNTHETIC-NO-GAME'
                selection.state_dir = root / 'synthetic-state'
                selection.prepared = {'preparation': {}}
                selection.case = {'id': case, 'budgets': {'readiness_timeout': 400, 'timeout': 5400}}
                selection.adapter_path = Path(adapter.__file__)
                selection.preflight = Mock(return_value={'blockers': []})
                selection.load_adapter = Mock(return_value=adapter)
                selection.adapter_context = Mock(return_value={'case': case})
                clients = []
                captured_receipts = {}
                original_client_type = client_source.CaseClient

                def make_client(actual_selection):
                    self.assertIs(actual_selection, selection)
                    client = original_client_type.__new__(original_client_type)
                    client.selection = selection
                    client.context = selection.context
                    client.live = selection.run_dir
                    client.state = selection.state_dir
                    client.output = selection.run_dir / 'case-output'
                    client.frozen = {'run_id': 'SYNTHETIC-NO-GAME', 'screen_task': 'synthetic-screen'}
                    client._handle = object()
                    client.read_report = Mock(return_value={'phase': 'hold', 'steps': []})
                    client.guard = Mock()
                    client.retain_held_process = Mock()
                    client.retain_process = Mock()
                    client.normal_close = Mock(return_value={'synthetic_close': True, 'business_pass': False})
                    client.close_handle = Mock()
                    client.wait_hold = Mock(wraps=client.wait_hold)
                    clients.append(client)
                    return client

                def first_observation(client, actual_prefix):
                    self.assertIs(client, clients[0])
                    self.assertEqual(actual_prefix, prefix)
                    for name in ('readiness-window.json', 'readiness-window-result.json'):
                        captured_receipts[name] = (client.output / name).read_bytes()
                    raise StopAtFirstObservation('SYNTHETIC-ADAPTER-ENTRY-ONLY')

                validation_boundary = (patch.object(adapter, 'validate_contract')
                                       if adapter is rmtm_adapter else nullcontext())
                with validation_boundary as validated, \
                     patch.object(entry, 'check_pin'), \
                     patch.object(entry.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as launch, \
                     patch.object(client_source, 'CaseClient', side_effect=make_client), \
                     patch.object(client_source.time, 'monotonic', return_value=100.0), \
                     patch.object(adapter, 'case_config', return_value={}), \
                     patch.object(adapter, 'observe', side_effect=first_observation) as observe, \
                     patch.object(adapter, 'original_day', side_effect=AssertionError('No business-day calls')) as day:
                    # The constructor is replaced, but readiness is the actual
                    # create-once implementation, not a permissive fake wait.
                    result = selection.run()

                client = clients[0]
                launch.assert_called_once()
                client.wait_hold.assert_called_once_with()
                observe.assert_called_once_with(client, prefix)
                day.assert_not_called()
                if adapter is rmtm_adapter:
                    validated.assert_called_once_with({'case': case}, require_prepared=True)
                client.normal_close.assert_called_once_with('business_failure_preserved')
                client.close_handle.assert_called_once_with()
                self.assertEqual(result['case_error'], 'StopAtFirstObservation: SYNTHETIC-ADAPTER-ENTRY-ONLY')
                self.assertEqual(result['business_acceptance'], 'RED_OR_INCOMPLETE')
                window = json.loads(captured_receipts['readiness-window.json'])
                ready = json.loads(captured_receipts['readiness-window-result.json'])
                self.assertEqual((window['budget_seconds'], window['deadline_monotonic']), (400, 500.0))
                self.assertEqual(client._readiness_limit, 500.0)
                self.assertEqual(ready['status'], 'READINESS_HOLD_OBSERVED')
                self.assertTrue(ready['within_original_deadline'])
                self.assertFalse(ready['business_pass'])
                for name, original in captured_receipts.items():
                    self.assertEqual((client.output / name).read_bytes(), original)


if __name__ == '__main__':
    main()
