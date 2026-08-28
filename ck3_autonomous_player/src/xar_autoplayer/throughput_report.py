"""Decompose one-generation wall time into an actionable throughput budget.

The one-generation report already records exact run/turn timestamps, gameplay
date deltas, durable checkpoint turn indices, and explicit cleanup duration.
That is enough to compare the complete steady-state turn loop with a target:
query turns, gameplay turns, planner/inter-turn gaps, and checkpoint-following
gaps all remain in the measured first-turn-start to last-turn-finish span.
The analyzer is read-only and cannot change war entry, continuation, surrender,
peace, or termination policy. Checkpoint time remains an honest inference: the
current report has no checkpoint start timestamp, so this analyzer attributes
the inter-turn gap immediately following a checkpointed turn to
``checkpoint_interturn`` rather than claiming pure save I/O time.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any


THROUGHPUT_ANALYSIS_VERSION = "one-generation-throughput-v3"
DEFAULT_HARD_TARGET_DAYS_PER_MINUTE = 60.0
DEFAULT_STRETCH_TARGET_DAYS_PER_MINUTE = 120.0
_RAW_UNITS_PER_GAME_DAY = 24


def analyze_one_generation_throughput(
    report: object,
    *,
    hard_target_days_per_minute: float = DEFAULT_HARD_TARGET_DAYS_PER_MINUTE,
    stretch_target_days_per_minute: float = DEFAULT_STRETCH_TARGET_DAYS_PER_MINUTE,
) -> dict[str, object]:
    """Return a turn-loop steady-state gate and full-run decomposition."""

    if not isinstance(report, dict):
        raise ValueError("one-generation report must be a JSON object")
    hard_target = _positive_rate(
        hard_target_days_per_minute,
        "hard_target_days_per_minute",
    )
    stretch_target = _positive_rate(
        stretch_target_days_per_minute,
        "stretch_target_days_per_minute",
    )
    if stretch_target < hard_target:
        raise ValueError(
            "stretch_target_days_per_minute must be at least the hard target"
        )

    started_at = _timestamp(report.get("started_at"), "report.started_at")
    finished_at = _timestamp(report.get("finished_at"), "report.finished_at")
    total_seconds = _nonnegative_interval(
        started_at, finished_at, "report elapsed interval"
    )
    reported_elapsed = report.get("elapsed_seconds")
    if isinstance(reported_elapsed, (int, float)) and not isinstance(
        reported_elapsed, bool
    ):
        if reported_elapsed < 0:
            raise ValueError("report.elapsed_seconds must be nonnegative")
        total_seconds = float(reported_elapsed)

    auto_run = report.get("auto_run")
    turns = auto_run.get("turns") if isinstance(auto_run, dict) else None
    if not isinstance(turns, list) or not turns:
        raise ValueError("one-generation report lacks auto_run.turns")

    checkpoint_rows = report.get("checkpoints")
    checkpoint_turn_indices: set[int] = set()
    if isinstance(checkpoint_rows, list):
        for row in checkpoint_rows:
            if not isinstance(row, dict):
                continue
            index = _plain_int(row.get("turn_index"))
            if index is not None and index > 0:
                checkpoint_turn_indices.add(index)

    normalized_turns: list[dict[str, object]] = []
    class_seconds: dict[str, float] = defaultdict(float)
    class_counts: dict[str, int] = defaultdict(int)
    timeline: dict[tuple[object, object, object], dict[str, float | int]] = {}
    game_days = 0.0
    advance_seconds = 0.0
    query_seconds = 0.0
    query_count = 0

    for position, raw_turn in enumerate(turns):
        if not isinstance(raw_turn, dict):
            raise ValueError(f"auto_run.turns[{position}] must be an object")
        turn_started = _timestamp(
            raw_turn.get("started_at"),
            f"auto_run.turns[{position}].started_at",
        )
        turn_finished = _timestamp(
            raw_turn.get("finished_at"),
            f"auto_run.turns[{position}].finished_at",
        )
        duration = _nonnegative_interval(
            turn_started,
            turn_finished,
            f"auto_run.turns[{position}] interval",
        )
        turn_class = raw_turn.get("class")
        class_name = turn_class if isinstance(turn_class, str) else "unknown"
        elapsed_days = _turn_elapsed_game_days(raw_turn)
        turn_index = _plain_int(raw_turn.get("index"))
        normalized_turns.append(
            {
                "index": turn_index,
                "started": turn_started,
                "finished": turn_finished,
                "duration": duration,
                "class": class_name,
                "elapsed_days": elapsed_days,
            }
        )
        class_seconds[class_name] += duration
        class_counts[class_name] += 1
        if class_name == "query":
            query_count += 1
            query_seconds += duration
        if elapsed_days <= 0:
            continue
        game_days += elapsed_days
        advance_seconds += duration
        result = raw_turn.get("result")
        result = result if isinstance(result, dict) else {}
        key = (
            result.get("timeline_speed"),
            result.get("requested_horizon_days"),
            result.get("timeline_policy"),
        )
        bucket = timeline.setdefault(
            key,
            {"count": 0, "game_days": 0.0, "wall_seconds": 0.0},
        )
        bucket["count"] = int(bucket["count"]) + 1
        bucket["game_days"] = float(bucket["game_days"]) + elapsed_days
        bucket["wall_seconds"] = float(bucket["wall_seconds"]) + duration

    first_started = normalized_turns[0]["started"]
    last_finished = normalized_turns[-1]["finished"]
    assert isinstance(first_started, datetime)
    assert isinstance(last_finished, datetime)
    startup_seconds = _nonnegative_interval(
        started_at, first_started, "startup interval"
    )
    turn_loop_steady_state_seconds = _nonnegative_interval(
        first_started,
        last_finished,
        "turn-loop steady-state interval",
    )
    post_turn_loop_tail_seconds = _nonnegative_interval(
        last_finished,
        finished_at,
        "post-turn-loop report tail",
    )

    checkpoint_gap_seconds = 0.0
    checkpoint_gap_count = 0
    ordinary_gap_seconds = 0.0
    ordinary_gap_count = 0
    for current, following in zip(normalized_turns, normalized_turns[1:]):
        current_finished = current["finished"]
        following_started = following["started"]
        assert isinstance(current_finished, datetime)
        assert isinstance(following_started, datetime)
        gap = _nonnegative_interval(
            current_finished, following_started, "inter-turn interval"
        )
        if current.get("index") in checkpoint_turn_indices:
            checkpoint_gap_seconds += gap
            checkpoint_gap_count += 1
        else:
            ordinary_gap_seconds += gap
            ordinary_gap_count += 1

    cleanup = report.get("cleanup")
    cleanup_seconds_value = (
        cleanup.get("elapsed_seconds") if isinstance(cleanup, dict) else None
    )
    cleanup_seconds = (
        float(cleanup_seconds_value)
        if isinstance(cleanup_seconds_value, (int, float))
        and not isinstance(cleanup_seconds_value, bool)
        and cleanup_seconds_value >= 0
        else 0.0
    )
    turn_execution_seconds = sum(class_seconds.values())
    accounted_seconds = (
        startup_seconds
        + turn_execution_seconds
        + checkpoint_gap_seconds
        + ordinary_gap_seconds
        + cleanup_seconds
    )
    residual_seconds = total_seconds - accounted_seconds

    fixed_seconds = startup_seconds + cleanup_seconds
    actual_days_per_minute = _rate(game_days, total_seconds)
    active_seconds = max(0.0, total_seconds - fixed_seconds)
    active_days_per_minute = _rate(game_days, active_seconds)
    advance_days_per_minute = _rate(game_days, advance_seconds)

    timeline_rows: list[dict[str, object]] = []
    for (speed, horizon, policy), bucket in sorted(
        timeline.items(), key=lambda item: repr(item[0])
    ):
        bucket_days = float(bucket["game_days"])
        bucket_seconds = float(bucket["wall_seconds"])
        timeline_rows.append(
            {
                "timeline_speed": speed,
                "requested_horizon_days": horizon,
                "timeline_policy": policy,
                "count": int(bucket["count"]),
                "game_days": _round(bucket_days),
                "wall_seconds": _round(bucket_seconds),
                "days_per_minute": _round(
                    _rate(bucket_days, bucket_seconds)
                ),
            }
        )

    return {
        "format_version": 3,
        "kind": THROUGHPUT_ANALYSIS_VERSION,
        "run_id": report.get("run_id"),
        "source_status": report.get("status"),
        "game_days": _round(game_days),
        "wall_seconds": _round(total_seconds),
        "actual_days_per_minute": _round(actual_days_per_minute),
        "turn_loop_steady_state_days_per_minute": _round(
            _rate(game_days, turn_loop_steady_state_seconds)
        ),
        "active_days_per_minute_excluding_startup_cleanup": _round(
            active_days_per_minute
        ),
        "advance_only_days_per_minute": _round(advance_days_per_minute),
        "targets": {
            "hard": _target_budget(
                target_days_per_minute=hard_target,
                game_days=game_days,
                turn_loop_steady_state_seconds=(
                    turn_loop_steady_state_seconds
                ),
                total_seconds=total_seconds,
                fixed_seconds=fixed_seconds,
                turn_loop_days_per_minute=_rate(
                    game_days, turn_loop_steady_state_seconds
                ),
                actual_days_per_minute=actual_days_per_minute,
            ),
            "stretch": _target_budget(
                target_days_per_minute=stretch_target,
                game_days=game_days,
                turn_loop_steady_state_seconds=(
                    turn_loop_steady_state_seconds
                ),
                total_seconds=total_seconds,
                fixed_seconds=fixed_seconds,
                turn_loop_days_per_minute=_rate(
                    game_days, turn_loop_steady_state_seconds
                ),
                actual_days_per_minute=actual_days_per_minute,
            ),
        },
        "decomposition": {
            "startup_seconds": _round(startup_seconds),
            "turn_loop_steady_state_seconds": _round(
                turn_loop_steady_state_seconds
            ),
            "post_last_turn_to_report_finish_seconds": _round(
                post_turn_loop_tail_seconds
            ),
            "query": {
                "count": query_count,
                "seconds": _round(query_seconds),
            },
            "advance": {
                "count": sum(int(row["count"]) for row in timeline_rows),
                "game_days": _round(game_days),
                "seconds": _round(advance_seconds),
            },
            "turn_class_counts": dict(sorted(class_counts.items())),
            "turn_class_seconds": {
                key: _round(value) for key, value in sorted(class_seconds.items())
            },
            "checkpoint_interturn": {
                "report_checkpoint_count": len(checkpoint_turn_indices),
                "measured_gap_count": checkpoint_gap_count,
                "seconds": _round(checkpoint_gap_seconds),
                "average_seconds": _round(
                    checkpoint_gap_seconds / checkpoint_gap_count
                    if checkpoint_gap_count
                    else 0.0
                ),
                "precision": "inferred_from_post_turn_gap",
            },
            "ordinary_interturn": {
                "gap_count": ordinary_gap_count,
                "seconds": _round(ordinary_gap_seconds),
            },
            "cleanup_seconds": _round(cleanup_seconds),
            "residual_seconds": _round(residual_seconds),
        },
        "timeline_breakdown": timeline_rows,
        "measurement_quality": {
            "startup": "exact_report_and_first_turn_timestamps",
            "turn_execution": "exact_turn_timestamps",
            "game_days": "turn_elapsed_days_or_exact_date_delta",
            "checkpoint": "inferred_from_checkpoint_turn_interturn_gap",
            "turn_loop_steady_state": (
                "exact_first_recorded_turn_start_to_last_recorded_turn_finish"
            ),
            "post_turn_loop_tail": (
                "exact_interval_but_internal_failure_and_finalization_opaque"
            ),
            "cleanup": (
                "explicit_report_elapsed_seconds"
                if cleanup_seconds_value is not None
                else "unavailable_assumed_zero"
            ),
            "report_is_sufficient_for_budget": True,
            "report_is_sufficient_for_pure_checkpoint_io": False,
        },
        "policy_neutrality": {
            "read_only_report_analysis": True,
            "changes_gameplay_decisions": False,
            "measurement_scope": (
                "all recorded query/gameplay turn execution and inter-turn "
                "gaps from first turn start through last turn finish"
            ),
            "war_contracts_unchanged": [
                "entry",
                "participation",
                "continuation",
                "surrender",
                "peace",
                "termination",
            ],
        },
    }


def _turn_elapsed_game_days(turn: dict[str, object]) -> float:
    result = turn.get("result")
    result = result if isinstance(result, dict) else {}
    elapsed = result.get("elapsed_days")
    if (
        isinstance(elapsed, (int, float))
        and not isinstance(elapsed, bool)
        and elapsed >= 0
    ):
        return float(elapsed)
    before = turn.get("before")
    after = turn.get("after")
    before_raw = _plain_int(before.get("date_raw")) if isinstance(before, dict) else None
    after_raw = _plain_int(after.get("date_raw")) if isinstance(after, dict) else None
    if before_raw is None or after_raw is None or after_raw <= before_raw:
        return 0.0
    delta = after_raw - before_raw
    if delta % _RAW_UNITS_PER_GAME_DAY != 0:
        raise ValueError("turn date delta is not a whole number of game days")
    return float(delta // _RAW_UNITS_PER_GAME_DAY)


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be an ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{field} is not valid ISO-8601") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def _nonnegative_interval(start: datetime, end: datetime, field: str) -> float:
    seconds = (end - start).total_seconds()
    if seconds < 0:
        raise ValueError(f"{field} must be nonnegative")
    return seconds


def _plain_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _rate(game_days: float, seconds: float) -> float:
    return game_days * 60.0 / seconds if game_days > 0 and seconds > 0 else 0.0


def _positive_rate(value: object, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
    ):
        raise ValueError(f"{field} must be positive")
    return float(value)


def _target_budget(
    *,
    target_days_per_minute: float,
    game_days: float,
    turn_loop_steady_state_seconds: float,
    total_seconds: float,
    fixed_seconds: float,
    turn_loop_days_per_minute: float,
    actual_days_per_minute: float,
) -> dict[str, object]:
    seconds_per_day = 60.0 / target_days_per_minute
    allowed_span_seconds = game_days * seconds_per_day
    return {
        "measurement_scope": "turn_loop_steady_state",
        "days_per_minute": _round(target_days_per_minute),
        "seconds_per_game_day": _round(seconds_per_day),
        "allowed_turn_loop_steady_state_seconds": _round(allowed_span_seconds),
        "turn_loop_budget_gap_seconds": _round(
            turn_loop_steady_state_seconds - allowed_span_seconds
        ),
        "target_met": turn_loop_days_per_minute >= target_days_per_minute,
        "full_run_diagnostic": {
            "days_per_minute": _round(actual_days_per_minute),
            "target_met": actual_days_per_minute >= target_days_per_minute,
            "budget_gap_seconds": _round(total_seconds - allowed_span_seconds),
            "startup_cleanup_seconds": _round(fixed_seconds),
        },
        "minimum_game_days_to_amortize_startup_cleanup": _round(
            fixed_seconds / seconds_per_day
        ),
    }


def _round(value: float) -> float:
    return round(float(value), 3)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xar-throughput-report",
        description=(
            "decompose one-generation report wall time and compare it with "
            "a complete turn-loop steady-state game-days-per-minute target"
        ),
    )
    parser.add_argument("report", type=Path, help="one-generation report.json")
    parser.add_argument(
        "--hard-target-days-per-minute",
        type=float,
        default=DEFAULT_HARD_TARGET_DAYS_PER_MINUTE,
    )
    parser.add_argument(
        "--stretch-target-days-per-minute",
        type=float,
        default=DEFAULT_STRETCH_TARGET_DAYS_PER_MINUTE,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        report = json.loads(arguments.report.read_text(encoding="utf-8"))
        result = analyze_one_generation_throughput(
            report,
            hard_target_days_per_minute=arguments.hard_target_days_per_minute,
            stretch_target_days_per_minute=(
                arguments.stretch_target_days_per_minute
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_HARD_TARGET_DAYS_PER_MINUTE",
    "DEFAULT_STRETCH_TARGET_DAYS_PER_MINUTE",
    "THROUGHPUT_ANALYSIS_VERSION",
    "analyze_one_generation_throughput",
    "main",
]
