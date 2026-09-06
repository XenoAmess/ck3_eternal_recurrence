#!/usr/bin/env python3
"""Focused contracts for the army-less Phase 2 activation sentinel."""

from __future__ import annotations

from copy import deepcopy

from zg361_phase2_date_sentinel_activation import (
    ARM_CAPABILITY,
    STATUS_CAPABILITY,
    STATUS_STEP,
    DateSentinelActivationError,
    run_date_only_daily_activation,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


def sentinel_status(*, state: str, observed_date: int) -> dict[str, object]:
    triggered = state == "triggered"
    return {
        "state": state,
        "generation": 7,
        "starting_date_raw": 1000,
        "target_date_raw": 1024,
        "last_observed_date_raw": observed_date,
        "trigger_date_raw": observed_date if triggered else 0,
        "speed": 5,
        "mode": "terminal_or_sentinel",
        "army_count": 0,
        "combat_count": 0,
        "completed_daily_ticks": 1 if triggered else 0,
        "intermediate_pause_count": 0,
        "trigger_flags": 1 if triggered else 0,
        "trigger_reasons": ["date_deadline"] if triggered else [],
        "signed_date_delta_from_target_raw": 0,
        "overshoot_days": 0 if triggered else -1,
        "pause_wrapper_called": triggered,
        "pause_observed": triggered,
        "terminal_observed": False,
        "abnormal": False,
    }


class FakeService:
    def __init__(self, *, overshoot: bool = False, bad_arm: bool = False) -> None:
        self.driver = self
        self.date_raw = 1000
        self.paused = True
        self.overshoot = overshoot
        self.bad_arm = bad_arm
        self.steps: list[tuple[str, str | None]] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": f"native:{self.date_raw}",
            "revision": 8,
            "native_revision": 8,
            "date_raw": self.date_raw,
            "paused": self.paused,
            "map_ready": True,
            "speed": 5,
            "player_armies": [],
            "active_event": (
                {"source": "native", "instance_id": 91, "option_count": 1}
                if self.date_raw == 1024
                else None
            ),
        }

    def _execute_primitive_step(
        self,
        step: str,
        *,
        expected_revision: int | None,
        required_capability: str | None = None,
        timeout_seconds: float,
        internal_semantic_snapshot: bool,
    ) -> dict[str, object]:
        require(expected_revision is None, "date sentinel bound a public revision")
        require(timeout_seconds > 0, "date sentinel used an expired timeout")
        require(internal_semantic_snapshot, "date sentinel lost internal semantics")
        self.steps.append((step, required_capability))
        if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            status = sentinel_status(state="armed", observed_date=1000)
            if self.bad_arm:
                status["army_count"] = 1
            return {
                "step": step,
                "accepted": True,
                "status": "available",
                "tactical_daily_sentinel": status,
            }
        if step == "resume-map":
            self.date_raw = 1048 if self.overshoot else 1024
            self.paused = True
            return {"step": step, "accepted": True, "status": "submitted"}
        require(step == STATUS_STEP, f"unexpected primitive step: {step}")
        return {
            "step": step,
            "accepted": True,
            "status": "available",
            "tactical_daily_sentinel": sentinel_status(
                state="triggered", observed_date=1024
            ),
        }


def starting_snapshot(*, armies: list[object] | None = None) -> dict[str, object]:
    return {
        "snapshot_id": "native:7",
        "revision": 7,
        "native_revision": 7,
        "date_raw": 1000,
        "paused": True,
        "map_ready": True,
        "speed": 5,
        "player_armies": [] if armies is None else armies,
        "active_event": None,
    }


def test_exact_one_day_stop_is_green() -> None:
    service = FakeService()
    timer = FakeClock()
    evidence = run_date_only_daily_activation(
        service,
        starting_snapshot(),
        speed=5,
        timeout_seconds=2.0,
        clock=timer.clock,
        sleeper=timer.sleep,
    )
    require(evidence["result"] == "GREEN", f"sentinel RED: {evidence}")
    require(
        evidence["target_date_raw"] == 1024
        and evidence["resume_submission_count"] == 1
        and evidence["external_pause_used"] is False,
        f"sentinel evidence drifted: {evidence}",
    )
    require(
        service.steps
        == [
            (
                "research-arm-tactical-daily-sentinel-v1-1000-to-1024-speed-5-mode-terminal-a-0",
                ARM_CAPABILITY,
            ),
            ("resume-map", None),
            (STATUS_STEP, STATUS_CAPABILITY),
        ],
        f"sentinel command sequence drifted: {service.steps}",
    )


def test_date_only_contract_rejects_player_armies() -> None:
    service = FakeService()
    timer = FakeClock()
    try:
        run_date_only_daily_activation(
            service,
            starting_snapshot(armies=[{"army_id": 17}]),
            speed=5,
            timeout_seconds=2.0,
            clock=timer.clock,
            sleeper=timer.sleep,
        )
    except DateSentinelActivationError as error:
        require(
            error.evidence["state"] == "unexpected_player_armies",
            f"army rejection drifted: {error.evidence}",
        )
    else:
        raise AssertionError("date-only sentinel accepted a player army")


def test_date_overshoot_fails_before_status_query() -> None:
    service = FakeService(overshoot=True)
    timer = FakeClock()
    try:
        run_date_only_daily_activation(
            service,
            starting_snapshot(),
            speed=5,
            timeout_seconds=2.0,
            clock=timer.clock,
            sleeper=timer.sleep,
        )
    except DateSentinelActivationError as error:
        require(
            error.evidence["state"] == "date_overshoot",
            f"overshoot evidence drifted: {error.evidence}",
        )
    else:
        raise AssertionError("date-only sentinel false-GREENed an overshoot")
    require(
        all(step != STATUS_STEP for step, _capability in service.steps),
        "overshot sentinel queried a misleading terminal status",
    )


def test_arm_ack_requires_zero_watched_armies() -> None:
    service = FakeService(bad_arm=True)
    timer = FakeClock()
    try:
        run_date_only_daily_activation(
            service,
            starting_snapshot(),
            speed=5,
            timeout_seconds=2.0,
            clock=timer.clock,
            sleeper=timer.sleep,
        )
    except DateSentinelActivationError as error:
        require(
            error.evidence["state"] == "arm_contract_red"
            and error.evidence["arm_checks"]["zero_armies"] is False,
            f"arm RED evidence drifted: {error.evidence}",
        )
    else:
        raise AssertionError("date-only sentinel accepted an army-bound ack")


def main() -> int:
    test_exact_one_day_stop_is_green()
    test_date_only_contract_rejects_player_armies()
    test_date_overshoot_fails_before_status_query()
    test_arm_ack_requires_zero_watched_armies()
    print("GREEN: Phase 2 date-only activation sentinel is exact and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
