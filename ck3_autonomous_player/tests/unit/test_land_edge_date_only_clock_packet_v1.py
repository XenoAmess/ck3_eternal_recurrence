"""Software Native packet boundary, never Game/pipe/OS or live qualification."""
import copy
import inspect
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge import clock_observation_timing_v1 as timing


def run_clock(*, wrong_stop_generation=False):
    fixture = json.loads((Path(__file__).parent / "fixtures" /
        "war4892_retained_land_edge_actual_v1.json").read_bytes())
    start = fixture["snapshot"]
    date = start["date_raw"]

    def status(stopped):
        reasons = ["date_deadline"] if stopped else []
        return {
            "state": "triggered" if stopped else "armed", "generation": 18 if stopped and wrong_stop_generation else 17,
            "starting_date_raw": date, "target_date_raw": date + 24,
            "last_observed_date_raw": date + 24 if stopped else date,
            "trigger_date_raw": date + 24 if stopped else 0, "speed": 1,
            "mode": "terminal_or_sentinel", "army_count": 0, "combat_count": 0,
            "completed_daily_ticks": int(stopped), "intermediate_pause_count": 0,
            "trigger_flags": sum(1 << nd._TACTICAL_DAILY_SENTINEL_TRIGGER_REASONS.index(r) for r in reasons),
            "trigger_reasons": reasons, "signed_date_delta_from_target_raw": 0,
            "overshoot_days": 0 if stopped else -1,
            "pause_wrapper_called": stopped, "pause_observed": stopped,
            "terminal_observed": False, "abnormal": False,
        }

    class Clock:
        # The actual current production clock and its real arm/stop validators
        # run. Only Native scheduling/returns and timing OS observers are fakes.
        _advance_exact_day_with_sentinel = nd.NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel
        command_timeout_seconds = life_advance_timeout_seconds = 1

        def __init__(self):
            self.current, self.commands = copy.deepcopy(start), []

        def take_internal_semantic_snapshot(self):
            return copy.deepcopy(self.current)

        def _execute_composite_primitive(self, step, current):
            self.commands.append(step)
            assert step == "set-speed-1"
            self.current["speed"] = 1
            return {"step": step, "accepted": True}

        def _execute_primitive_step(self, step, **kwargs):
            self.commands.append(step)
            if step.startswith(nd._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX):
                return {"step": step, "accepted": True, "status": "canceled"}
            stopped = step == nd._TACTICAL_DAILY_SENTINEL_STATUS_STEP
            return {"step": step, "accepted": True, "status": "available",
                    "tactical_daily_sentinel": status(stopped)}

        def _wait_for_life_advance_snapshot(self, current, predicate, **kwargs):
            assert predicate(current)
            return current

        def _resume_life_advance(self, current, actions, **kwargs):
            assert kwargs == {"native_stop_target_date_raw": date + 24}
            self.commands.append("resume-map")
            self.current.update(date_raw=date + 24, paused=True,
                native_revision=start["native_revision"] + 1,
                revision=start["revision"] + 1)
            return self.take_internal_semantic_snapshot()

        def _pause_life_advance(self, current, actions):
            self.commands.append("cleanup-pause-map")
            self.current["paused"] = True
            return self.take_internal_semantic_snapshot()

    driver = Clock()
    with patch.object(timing, "start_clock_observation_v1", return_value=None), \
         patch.object(timing, "finish_clock_observation_v1"), \
         patch.object(nd, "start_army_timing", return_value=None), \
         patch.object(nd, "finish_army_timing"):
        result = driver._advance_exact_day_with_sentinel(start, speed=1, actions=[])
    return driver, result


def test_current_exact_day_emits_only_date_a0_packet_at_unchanged_speed1():
    driver, (frame, receipt) = run_clock()
    arm = nd._TACTICAL_DAILY_SENTINEL_ARM_PREFIX + "53192808-to-53192832-speed-1-mode-terminal-a-0"
    assert driver.commands == ["set-speed-1", arm, "resume-map", nd._TACTICAL_DAILY_SENTINEL_STATUS_STEP]
    assert frame["paused"] is True and frame["date_raw"] == 53192832
    assert receipt["armed"]["army_count"] == receipt["stopped"]["army_count"] == 0
    assert receipt["stopped"]["generation"] == receipt["armed"]["generation"] == 17
    assert receipt["stopped"]["terminal_observed"] is False
    # The selected public step passes exact_one_day=True; it does not bind aN.
    source = inspect.getsource(nd.NativeHeadlessGameplayDriver._execute_step_unrecorded)
    branch = source.split('if step == "life-advance-one-day":', 1)[1].split('\n        if ', 1)[0]
    assert "exact_one_day=True" in branch
    assert "exact_one_day_proof_kind=None" in branch
    assert "exact_one_day_preferred_speed=1" in branch


def test_wrong_native_stop_generation_is_rejected():
    with pytest.raises(nd.BridgeUnavailableError, match="generation/date/tick"):
        run_clock(wrong_stop_generation=True)
