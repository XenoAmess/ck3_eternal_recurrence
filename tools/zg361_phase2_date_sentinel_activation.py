#!/usr/bin/env python3
"""Run one fixture-activation day under the native daily sentinel.

This module is intentionally separate from the already-large Phase 2 seed
runner.  It owns only the measured R149 boundary: a paused, army-less manager
frame must advance exactly one day at speed five without Python polling being
responsible for the stop.
"""

from __future__ import annotations

import copy
from typing import Any, Callable


RAW_HOURS_PER_DAY = 24
ARM_CAPABILITY = "game.command.research-arm-tactical-daily-sentinel-v1-N"
STATUS_CAPABILITY = "game.command.research-query-tactical-daily-sentinel-v1"
STATUS_STEP = "research-query-tactical-daily-sentinel-v1"


class DateSentinelActivationError(RuntimeError):
    """A date-only native sentinel failed before an exact paused stop."""

    def __init__(self, message: str, evidence: dict[str, Any]) -> None:
        super().__init__(message)
        self.evidence = evidence


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _remaining(deadline: float, clock: Callable[[], float]) -> float:
    return max(0.001, deadline - clock())


def _status(result: object) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    value = result.get("tactical_daily_sentinel")
    return copy.deepcopy(value) if isinstance(value, dict) else None


def _fail(message: str, **evidence: object) -> DateSentinelActivationError:
    return DateSentinelActivationError(
        message,
        {
            "schema_version": 1,
            "kind": "zg361_phase2_date_only_activation_sentinel",
            "result": "RED",
            **evidence,
        },
    )


def run_date_only_daily_activation(
    service: Any,
    starting_snapshot: dict[str, Any],
    *,
    speed: int,
    timeout_seconds: float,
    clock: Callable[[], float],
    sleeper: Callable[[float], None],
) -> dict[str, Any]:
    """Advance one exact day and let the in-process sentinel pause CK3.

    R149 measured that one ordinary speed-five resume crossed five dates
    before the MCP observer could pause.  The manager had no player army, so
    the established battle sentinel is armed in its date-only ``a-0`` form.
    No external pause or gameplay query is issued while the map is running.
    """

    if isinstance(speed, bool) or speed not in range(1, 6):
        raise ValueError("date sentinel speed must be an integer from 1 to 5")
    if timeout_seconds <= 0:
        raise ValueError("date sentinel timeout must be positive")
    starting_date_raw = _integer(starting_snapshot.get("date_raw"))
    if not (
        starting_snapshot.get("map_ready") is True
        and starting_snapshot.get("paused") is True
        and starting_snapshot.get("speed") == speed
        and starting_date_raw is not None
        and starting_date_raw > 0
    ):
        raise _fail(
            "date sentinel requires an exact paused map-ready speed binding",
            state="invalid_starting_snapshot",
            starting_snapshot=starting_snapshot,
            requested_speed=speed,
        )
    if starting_snapshot.get("player_armies") not in (None, []):
        raise _fail(
            "date-only activation requires an army-less player snapshot",
            state="unexpected_player_armies",
            starting_snapshot=starting_snapshot,
        )

    driver = getattr(service, "driver", None)
    primitive = getattr(driver, "_execute_primitive_step", None)
    if not callable(primitive):
        raise _fail(
            "native primitive transport is unavailable",
            state="primitive_transport_unavailable",
        )

    target_date_raw = starting_date_raw + RAW_HOURS_PER_DAY
    arm_step = (
        "research-arm-tactical-daily-sentinel-v1-"
        f"{starting_date_raw}-to-{target_date_raw}-speed-{speed}-"
        "mode-terminal-a-0"
    )
    deadline = clock() + timeout_seconds
    arm_result = primitive(
        arm_step,
        expected_revision=None,
        required_capability=ARM_CAPABILITY,
        timeout_seconds=_remaining(deadline, clock),
        internal_semantic_snapshot=True,
    )
    arm_status = _status(arm_result)
    arm_checks = {
        "ack_available": (
            isinstance(arm_result, dict)
            and arm_result.get("accepted") is True
            and arm_result.get("status") == "available"
        ),
        "state_armed": (
            isinstance(arm_status, dict) and arm_status.get("state") == "armed"
        ),
        "generation_positive": (
            isinstance(arm_status, dict)
            and (_integer(arm_status.get("generation")) or 0) > 0
        ),
        "starting_date_exact": (
            isinstance(arm_status, dict)
            and arm_status.get("starting_date_raw") == starting_date_raw
        ),
        "target_date_exact": (
            isinstance(arm_status, dict)
            and arm_status.get("target_date_raw") == target_date_raw
        ),
        "speed_exact": (
            isinstance(arm_status, dict) and arm_status.get("speed") == speed
        ),
        "terminal_mode": (
            isinstance(arm_status, dict)
            and arm_status.get("mode") == "terminal_or_sentinel"
        ),
        "zero_armies": (
            isinstance(arm_status, dict) and arm_status.get("army_count") == 0
        ),
        "zero_combats": (
            isinstance(arm_status, dict) and arm_status.get("combat_count") == 0
        ),
    }
    if not all(arm_checks.values()):
        raise _fail(
            "date-only sentinel arm acknowledgement is inconsistent",
            state="arm_contract_red",
            arm_step=arm_step,
            arm_result=arm_result,
            arm_checks=arm_checks,
        )

    resume_result = primitive(
        "resume-map",
        expected_revision=None,
        timeout_seconds=_remaining(deadline, clock),
        internal_semantic_snapshot=True,
    )
    if not (
        isinstance(resume_result, dict)
        and resume_result.get("accepted") is True
    ):
        raise _fail(
            "date-only sentinel resume was not accepted",
            state="resume_contract_red",
            arm_step=arm_step,
            arm_result=arm_result,
            resume_result=resume_result,
        )

    final_snapshot: dict[str, Any] | None = None
    while clock() < deadline:
        observed = service.snapshot()
        if not isinstance(observed, dict):
            raise _fail(
                "date-only sentinel observed a non-object snapshot",
                state="snapshot_contract_red",
            )
        observed_date_raw = _integer(observed.get("date_raw"))
        if observed_date_raw is not None and observed_date_raw > target_date_raw:
            raise _fail(
                "date-only sentinel crossed its exact target date",
                state="date_overshoot",
                target_date_raw=target_date_raw,
                observed_snapshot=observed,
            )
        if (
            observed_date_raw == target_date_raw
            and observed.get("paused") is True
        ):
            final_snapshot = observed
            break
        sleeper(0.01)
    if final_snapshot is None:
        raise _fail(
            "date-only sentinel did not publish an exact paused stop",
            state="paused_stop_timeout",
            target_date_raw=target_date_raw,
            arm_step=arm_step,
            arm_result=arm_result,
            resume_result=resume_result,
        )

    status_result: dict[str, Any] | None = None
    final_status: dict[str, Any] | None = None
    while clock() < deadline:
        queried = primitive(
            STATUS_STEP,
            expected_revision=None,
            required_capability=STATUS_CAPABILITY,
            timeout_seconds=_remaining(deadline, clock),
            internal_semantic_snapshot=True,
        )
        status_result = queried if isinstance(queried, dict) else None
        candidate = _status(queried)
        if isinstance(candidate, dict) and candidate.get("state") in {
            "triggered",
            "failed",
        }:
            final_status = candidate
            break
        sleeper(0.01)

    trigger_reasons = (
        final_status.get("trigger_reasons")
        if isinstance(final_status, dict)
        else None
    )
    stop_checks = {
        "state_triggered": (
            isinstance(final_status, dict)
            and final_status.get("state") == "triggered"
            and final_status.get("abnormal") is False
        ),
        "generation_exact": (
            isinstance(final_status, dict)
            and final_status.get("generation") == arm_status.get("generation")
        ),
        "target_date_exact": (
            isinstance(final_status, dict)
            and final_status.get("trigger_date_raw") == target_date_raw
            and final_status.get("last_observed_date_raw") == target_date_raw
        ),
        "one_daily_tick": (
            isinstance(final_status, dict)
            and final_status.get("completed_daily_ticks") == 1
        ),
        "deadline_reason": (
            isinstance(trigger_reasons, list)
            and "date_deadline" in trigger_reasons
        ),
        "zero_overshoot": (
            isinstance(final_status, dict)
            and final_status.get("overshoot_days") == 0
            and final_status.get("signed_date_delta_from_target_raw") == 0
        ),
        "pause_observed": (
            isinstance(final_status, dict)
            and final_status.get("pause_observed") is True
        ),
        "zero_armies": (
            isinstance(final_status, dict)
            and final_status.get("army_count") == 0
            and final_status.get("combat_count") == 0
        ),
        "final_snapshot_exact": (
            final_snapshot.get("date_raw") == target_date_raw
            and final_snapshot.get("paused") is True
        ),
    }
    if not all(stop_checks.values()):
        raise _fail(
            "date-only sentinel stop contract is inconsistent",
            state="stop_contract_red",
            arm_step=arm_step,
            arm_result=arm_result,
            resume_result=resume_result,
            status_result=status_result,
            final_snapshot=final_snapshot,
            stop_checks=stop_checks,
        )

    return {
        "schema_version": 1,
        "kind": "zg361_phase2_date_only_activation_sentinel",
        "result": "GREEN",
        "starting_date_raw": starting_date_raw,
        "target_date_raw": target_date_raw,
        "speed": speed,
        "arm_step": arm_step,
        "arm_result": arm_result,
        "resume_result": resume_result,
        "status_result": status_result,
        "final_snapshot": final_snapshot,
        "arm_checks": arm_checks,
        "stop_checks": stop_checks,
        "external_pause_used": False,
        "resume_submission_count": 1,
    }
