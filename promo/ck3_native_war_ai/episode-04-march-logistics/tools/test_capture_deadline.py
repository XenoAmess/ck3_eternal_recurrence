"""Synthetic offline deadline regressions; no game, process, screen or media."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_deadline import RecordingDeadlineGuard, recording_deadline_guard


class Clock:
    def __init__(self):
        self.wall = datetime(2026, 10, 16, 7, 40, tzinfo=timezone.utc)
        self.mono = 1000.0

    def advance(self, seconds):
        self.wall += timedelta(seconds=seconds)
        self.mono += seconds


def guard(clock, capacity_seconds=600, **kwargs):
    kwargs.setdefault("capacity_check", lambda: None)  # Synthetic fixture, no actual capacity grant.
    return RecordingDeadlineGuard(machine_id="synthetic-deadline-test-machine",
        absolute_deadlines=[{"source": "synthetic-actual-quota",
            "deadline_utc": (clock.wall + timedelta(seconds=capacity_seconds)).isoformat()}],
        clock=lambda: clock.wall, monotonic=lambda: clock.mono, **kwargs)


def test_near_deadline_90second_recording_rejected_before_any_attempt():
    clock = Clock()
    subject = guard(clock, capacity_seconds=12)
    subject.bind_session_timeout(12)
    with pytest.raises(ValueError, match="recording=90s.*normal-close-reserve=120s"):
        subject(90)


def test_warmup_consumes_original_session_budget_and_cannot_renew_it():
    clock = Clock()
    subject = guard(clock)
    subject.bind_session_timeout(300)
    clock.advance(91)  # Frontend warm-up and final load, before map-ready.
    assert subject(89)["session_elapsed_before_recording_seconds"] == 91
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)
    with pytest.raises(ValueError, match="already bound"):
        subject.bind_session_timeout(300)


def test_session_deadline_is_earlier_than_capacity_deadline():
    clock = Clock()
    subject = guard(clock, capacity_seconds=900)
    subject.bind_session_timeout(210)
    actual = subject(90)
    assert actual["remaining_seconds"] == actual["required_remaining_seconds"] == 210
    assert actual["machine_id"] == "synthetic-deadline-test-machine"
    assert actual["deadline_renewed"] is False
    clock.advance(0.001)
    with pytest.raises(ValueError, match="deadline insufficient"):
        subject(90)


def test_capacity_deadline_is_earlier_than_supervisor_timeout():
    clock = Clock()
    subject = guard(clock, capacity_seconds=209)
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)


def capacity_receipt(tmp_path, clock, seconds=600, **changes):
    scene = tmp_path / "synthetic-scene"
    scene.mkdir(exist_ok=True)
    run = scene / "synthetic-run"
    row = {"admitted": True, "machine_id": "synthetic-deadline-test-machine",
           "scene_root": str(scene), "run_id": run.name, "source_head": "a" * 40,
           "quota_review_at_utc": (clock.wall + timedelta(seconds=seconds)).isoformat(), **changes}
    path = tmp_path / ("capacity-" + str(len(list(tmp_path.glob("capacity-*.json")))) + ".json")
    path.write_text(json.dumps(row), encoding="utf-8")
    admission = [str(path), hashlib.sha256(path.read_bytes()).hexdigest()]
    return admission, {"assets_root": str(scene)}, run


def test_later_cli_deadline_never_extends_capacity_receipt(tmp_path):
    clock = Clock()
    admission, prepared, run = capacity_receipt(tmp_path, clock, 209)
    args = SimpleNamespace(recording_deadline_utc=(clock.wall + timedelta(days=1)).isoformat(),
                           recording_capacity_admission=admission)
    subject = recording_deadline_guard(args, machine_id="synthetic-deadline-test-machine",
        prepared=prepared, run_dir=run, source_head="a" * 40,
        clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)


def test_backward_wall_clock_does_not_extend_capacity():
    clock = Clock()
    subject = guard(clock, capacity_seconds=220)
    subject.bind_session_timeout(21600)
    clock.advance(11)
    clock.wall -= timedelta(hours=1)
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)


def test_forward_wall_clock_shortens_capacity_immediately():
    clock = Clock()
    subject = guard(clock, capacity_seconds=220)
    subject.bind_session_timeout(21600)
    clock.wall += timedelta(seconds=11)
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)


def test_missing_capacity_deadline_blocks_start_but_not_guard_construction():
    clock = Clock()
    subject = RecordingDeadlineGuard(machine_id="synthetic-deadline-test-machine",
        clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="explicit absolute capacity deadline"):
        subject(1)


def test_unbound_session_blocks_start():
    with pytest.raises(ValueError, match="has not been bound"):
        guard(Clock())(90)


@pytest.mark.parametrize("reserve", [0, -1, 119.999, float("nan"), float("inf"), True])
def test_normal_close_reserve_cannot_be_disabled(reserve):
    with pytest.raises(ValueError):
        guard(Clock(), close_reserve_seconds=reserve)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True])
def test_invalid_supervisor_timeout_is_rejected(timeout):
    with pytest.raises(ValueError, match="finite and positive"):
        guard(Clock()).bind_session_timeout(timeout)


@pytest.mark.parametrize("seconds", [0, -1, 3601, 90.0, True])
def test_invalid_recording_duration_is_rejected(seconds):
    subject = guard(Clock())
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="integer"):
        subject(seconds)


def test_naive_absolute_deadline_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        RecordingDeadlineGuard(machine_id="synthetic-deadline-test-machine",
            absolute_deadlines=[{"source": "synthetic-cli", "deadline_utc": "2026-10-16T07:45:01"}])


def test_capacity_metadata_is_checked_again_for_each_admission():
    clock = Clock()
    checks = []
    subject = guard(clock, capacity_check=lambda: checks.append(True))
    subject.bind_session_timeout(600)
    subject(90)
    clock.advance(1)
    subject(90)
    assert checks == [True, True]


def test_other_machine_capacity_is_rejected(tmp_path):
    clock = Clock()
    admission, prepared, run = capacity_receipt(tmp_path, clock,
                                               machine_id="synthetic-other-machine")
    with pytest.raises(ValueError, match="another machine"):
        recording_deadline_guard(SimpleNamespace(recording_capacity_admission=admission),
            machine_id="synthetic-deadline-test-machine", prepared=prepared, run_dir=run,
            clock=lambda: clock.wall)


@pytest.mark.parametrize(("change", "message"), [
    ({"run_id": "synthetic-other-run"}, "another run"),
    ({"scene_root": "/synthetic-other-scene"}, "another scene"),
    ({"source_head": "b" * 40}, "another source commit"),
    ({"admitted": False}, "not actually admitted"),
])
def test_capacity_scope_mismatch_is_rejected(tmp_path, change, message):
    clock = Clock()
    admission, prepared, run = capacity_receipt(tmp_path, clock, **change)
    with pytest.raises(ValueError, match=message):
        recording_deadline_guard(SimpleNamespace(recording_capacity_admission=admission),
            machine_id="synthetic-deadline-test-machine", prepared=prepared, run_dir=run,
            source_head="a" * 40, clock=lambda: clock.wall)


def test_explicit_deadline_without_bound_capacity_cannot_grant_recording(tmp_path):
    clock = Clock()
    args = SimpleNamespace(recording_deadline_utc=(clock.wall + timedelta(hours=1)).isoformat())
    subject = recording_deadline_guard(args, machine_id="synthetic-deadline-test-machine",
        prepared={"assets_root": str(tmp_path)}, run_dir=tmp_path / "synthetic-run",
        clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="capacity admission PATH SHA256"):
        subject(90)


def test_capacity_exact_bytes_rechecked_before_second_start_admission(tmp_path):
    clock = Clock()
    admission, prepared, run = capacity_receipt(tmp_path, clock)
    subject = recording_deadline_guard(SimpleNamespace(recording_capacity_admission=admission),
        machine_id="synthetic-deadline-test-machine", prepared=prepared, run_dir=run,
        clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    subject.bind_session_timeout(21600)
    first = subject(90)
    assert first["deadlines"][1]["capacity_admission"]["sha256"] == admission[1]
    Path(admission[0]).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="exact SHA changed"):
        subject(90)


def test_earlier_runtime_capacity_never_extended_by_second_receipt(tmp_path):
    clock = Clock()
    earlier, prepared, run = capacity_receipt(tmp_path, clock, seconds=209)
    later, _, _ = capacity_receipt(tmp_path, clock, seconds=900)
    subject = recording_deadline_guard(SimpleNamespace(recording_capacity_admission=later,
        runtime_capacity_admission=earlier), machine_id="synthetic-deadline-test-machine",
        prepared=prepared, run_dir=run, clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    subject.bind_session_timeout(21600)
    with pytest.raises(ValueError, match="remaining=209.000s"):
        subject(90)


def test_cli_parser_preserves_nonrecording_compatibility_and_accepts_new_limits():
    import capture_bootstrap
    arguments = ["run", "--prepared", "prepared", "--run-dir", "run",
        "--steam-offline-receipt", "offline", "--screen-cli", "screen",
        "--task-bus", "bus", "--screen-repo", "repository", "--screen-task-id", "synthetic-task",
        "--screen-expected-sequence", "1", "--screen-cli-sha256", "0" * 64]
    ordinary = capture_bootstrap.parser().parse_args(arguments)
    assert ordinary.recording_deadline_utc is None
    assert ordinary.recording_close_reserve_seconds == 120
    explicit = capture_bootstrap.parser().parse_args(arguments + [
        "--recording-deadline-utc", "2026-10-16T07:45:01Z",
        "--recording-close-reserve-seconds", "180"])
    assert explicit.recording_deadline_utc == "2026-10-16T07:45:01Z"
    assert explicit.recording_close_reserve_seconds == 180
