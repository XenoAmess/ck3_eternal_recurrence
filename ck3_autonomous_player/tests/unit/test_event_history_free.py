from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pytest


SOURCE = Path(os.environ.get('XAR_EVENT_TEST_SOURCE',
                             str(Path(__file__).resolve().parents[2] / 'src')))
sys.path.insert(0, str(SOURCE))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError


def _frame(revision: int, event_id: int | None, *, bridge_pid: int = 9):
    return {
        'revision': revision,
        'native_revision': revision,
        'snapshot_id': f'native:{revision}',
        'date_raw': 53171472,
        'map_ready': True,
        'paused': True,
        'episode_run_id': 'episode-1',
        'diagnostics': {'bridge_pid': bridge_pid, 'connection_generation': 3},
        'active_event': ({'instance_id': event_id, 'option_count': 1}
                         if event_id is not None else None),
    }


def _driver(starting, changed, calls):
    def primitive(step, **kwargs):
        calls.append(('primitive', step, kwargs))
        return {'accepted': True}

    def wait(snapshot, predicate, *, timeout_seconds):
        calls.append(('wait', snapshot, timeout_seconds))
        assert predicate(snapshot) is (changed['active_event'] is None or changed['active_event']['instance_id'] != starting['active_event']['instance_id'])
        return snapshot

    return SimpleNamespace(
        _driver_state_lock=threading.RLock(),
        _bookmark1070_material_frame=None,
        command_timeout_seconds=0.01,
        take_snapshot_without_native_command_history=lambda: calls.append(('starting',)) or starting,
        take_internal_semantic_snapshot=lambda: calls.append(('ending',)) or changed,
        take_snapshot=lambda: pytest.fail('full history snapshot used'),
        _execute_primitive_step=primitive,
        _wait_for_life_advance_snapshot=wait,
        _wait_for_snapshot=lambda *a, **kw: pytest.fail('full history wait used'),
    )


def test_native_event_uses_lean_frames_and_preserves_postcondition():
    calls = []
    fake = _driver(_frame(10, 5), _frame(11, None), calls)
    result = NativeHeadlessGameplayDriver._execute_event_option_step(
        fake, 'select-event-option-1', option_number=1, expected_revision=10)
    assert result['event_selection']['postcondition_verified'] is True
    assert result['event_selection']['old_event_instance_id'] == 5
    assert result['event_selection']['new_event_instance_id'] is None
    assert [row[0] for row in calls] == ['starting', 'primitive', 'ending', 'wait']
    assert calls[1][2]['include_native_command_history'] is False


@pytest.mark.parametrize('ending,reason', [
    (_frame(11, 5), 'ACK did not advance'),
    (_frame(11, None, bridge_pid=10), 'crossed its bridge'),
    ({**_frame(11, None), 'paused': False}, 'postcondition is not paused'),
])
def test_native_event_guards_remain(ending, reason):
    calls = []
    fake = _driver(_frame(10, 5), ending, calls)
    with pytest.raises(BridgeUnavailableError, match=reason):
        NativeHeadlessGameplayDriver._execute_event_option_step(
            fake, 'select-event-option-1', option_number=1, expected_revision=10)
    assert sum(row[0] == 'primitive' for row in calls) == 1


def test_semantic_wait_observes_later_event_revision_without_history():
    calls = []
    frames = iter([_frame(11, 5), _frame(12, None)])
    state = SimpleNamespace(
        capabilities=lambda: {'snapshot': True},
        wait_for_public_change=lambda revision, timeout: calls.append(('wait', revision, timeout)),
    )
    fake = SimpleNamespace(
        state=state,
        take_internal_semantic_snapshot=lambda: calls.append(('semantic',)) or next(frames),
        take_snapshot=lambda: pytest.fail('full history snapshot used'),
    )
    fake._wait_for_life_advance_change = lambda revision, *, timeout_seconds: (
        NativeHeadlessGameplayDriver._wait_for_life_advance_change(
            fake, revision, timeout_seconds=timeout_seconds))
    changed = NativeHeadlessGameplayDriver._wait_for_life_advance_snapshot(
        fake, _frame(10, 5),
        lambda frame: frame['active_event'] is None,
        timeout_seconds=0.1,
    )
    assert changed['revision'] == 12
    assert [row[0] for row in calls] == ['wait', 'semantic', 'wait', 'semantic']
    assert [row[1] for row in calls if row[0] == 'wait'] == [10, 11]


def test_service_selects_same_event_and_revision_with_lean_snapshot():
    calls = []
    fake = SimpleNamespace(
        snapshot=lambda **kwargs: calls.append(('snapshot', kwargs)) or _frame(10, 5),
        capabilities=lambda: {'action_steps': ['select-event-option-1']},
        execute_step=lambda step, **kwargs: calls.append(('execute', step, kwargs)) or {'accepted': True},
    )
    result = GameplayBridgeService.select_event_option(
        fake, 1, event_instance_id=5, expected_revision=10)
    assert result['event_instance_id'] == 5
    assert calls == [
        ('snapshot', {'include_native_command_history': False}),
        ('execute', 'select-event-option-1', {'expected_revision': 10}),
    ]
