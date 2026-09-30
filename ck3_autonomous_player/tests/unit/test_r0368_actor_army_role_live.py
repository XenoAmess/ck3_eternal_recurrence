"""Deterministic execution of the new worker path; no native process starts."""
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from xar_autoplayer import r0368_actor_army_role_live as entry
from xar_autoplayer.bridge.driver import BridgeUnavailableError


def _run(cleanup=True, available=True):
    keeper = Mock()
    keeper.abort = threading.Event()
    keeper.report.return_value = {'failure': None, 'thread_exited': True}
    driver = Mock()
    driver.take_snapshot.side_effect = [BridgeUnavailableError('loading'), {'paused': True}]
    inner = {'role_observed': available, 'query_attempts': 1, 'gameplay_actions': 0,
             'date_advance_actions': 0}
    called = []

    def native_session(spec, **kwargs):
        called.append(kwargs)
        kwargs['stop_event'].wait(5)
        return {'ok': True, 'shutdown': {'cleanup_proven': cleanup},
                'injector_attestation': {'complete_process_tree_proven': True}}

    with tempfile.TemporaryDirectory() as directory:
        with (patch('xar_autoplayer.bridge.native_driver.NativeHeadlessGameplayDriver', return_value=driver),
              patch('xar_autoplayer.native_session.native_session', side_effect=native_session),
              patch('xar_autoplayer.runtime.ck3_process_inventory', return_value={'processes': []}),
              patch.object(entry.role, '_git', return_value='a' * 40),
              patch.object(entry.role, '_fresh_target', return_value=True),
              patch.object(entry.role, 'collect_role_only_in_managed_session', return_value=inner) as collect):
            report = entry.run_owned_role_read(spec=SimpleNamespace(state_dir=Path(directory),
                profile_dir=Path(directory)), config=SimpleNamespace(pipe_name='test'),
                keeper=keeper, actor=29829, episode='exact-episode', war_id=16777231,
                army_id=83886367, output=Path(directory), timeout_seconds=2)
            collect.assert_called_once()
            driver.close.assert_called_once()
            keeper.stop.assert_called_once()
            if called[0]['before_process_create'] != keeper.process_create_gate:
                raise AssertionError('production creation gate was not forwarded')
            if entry.role.ROLE_ONLY_LIVE_AUTHORIZED:
                raise AssertionError('inner live flag remained set after exit')
            return report


def test_actual_worker_path_reads_once_then_cleans_up():
    result = _run()
    if (result['status'] != 'ROLE_READ_AVAILABLE' or result['query_attempts'] != 1
            or not result['managed_cleanup_verified']
            or result['gameplay_actions'] != 0 or result['date_advance_actions'] != 0):
        raise AssertionError(result)


def test_unproven_cleanup_never_completes_role_delivery():
    result = _run(cleanup=False)
    if result['status'] != 'RED' or result['managed_cleanup_verified']:
        raise AssertionError(result)


def test_partial_role_is_kept_distinct_from_available():
    result = _run(available=False)
    if result['status'] != 'ROLE_READ_PARTIAL_OR_UNAVAILABLE':
        raise AssertionError(result)
