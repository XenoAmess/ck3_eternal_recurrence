"""Backend-neutral execution loop for one-life gameplay turns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from .errors import AgentError


TurnPlanner = Callable[[list[dict[str, object]]], dict[str, object]]


class GameplayStepExecutor(Protocol):
    """Execute one planner-selected semantic gameplay step."""

    def execute_step(self, step: str) -> dict[str, object]: ...


@dataclass(frozen=True)
class CallableGameplayStepExecutor:
    """Adapt an existing step callback to the shared executor contract."""

    callback: Callable[[str], dict[str, object]]

    def execute_step(self, step: str) -> dict[str, object]:
        return self.callback(step)


RECOVERABLE_TURN_ERRORS = (
    "ordinary event interrupted",
    "one-life death terminal visible:",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _selected_step(
    turn: object, *, forbidden_steps: frozenset[str]
) -> tuple[dict[str, object], str]:
    if not isinstance(turn, dict):
        raise AgentError("one-life turn planner returned an invalid turn")
    selected = turn.get("selected_step")
    if not isinstance(selected, str) or selected in forbidden_steps:
        raise AgentError("one-life turn planner returned an invalid step")
    return turn, selected


def _execute_selected_step(
    executor: GameplayStepExecutor,
    selected_step: str,
    turn: dict[str, object],
) -> dict[str, object]:
    result = executor.execute_step(selected_step)
    if not isinstance(result, dict):
        raise AgentError("gameplay step executor returned an invalid result")
    decorated = dict(result)
    decorated["requested_step"] = "auto-turn"
    decorated["auto_turn"] = turn
    return decorated


def run_one_life_turn(
    commands: list[dict[str, object]],
    executor: GameplayStepExecutor,
    planner: TurnPlanner,
) -> dict[str, object]:
    """Plan and execute one semantic step through any gameplay backend."""
    turn, selected_step = _selected_step(
        planner(commands), forbidden_steps=frozenset({"auto-turn"})
    )
    return _execute_selected_step(executor, selected_step, turn)


def run_one_life_turns(
    commands: list[dict[str, object]],
    executor: GameplayStepExecutor,
    planner: TurnPlanner,
    turn_count: int,
    *,
    now: Callable[[], str] = _now,
) -> dict[str, object]:
    """Run a bounded sequence while preserving each planner decision/result."""
    if isinstance(turn_count, bool) or not isinstance(turn_count, int) or turn_count < 1:
        raise AgentError("one-life auto-run turn count must be positive")

    turns: list[dict[str, object]] = []
    status = "completed"
    for turn_index in range(1, turn_count + 1):
        turn, selected_step = _selected_step(
            planner(commands),
            forbidden_steps=frozenset({"auto-turn", "auto-run"}),
        )
        turn_record: dict[str, object] = {
            "index": turn_index,
            "command": "auto-turn",
            "started_at": now(),
            "ok": False,
        }
        try:
            turn_record["result"] = _execute_selected_step(
                executor, selected_step, turn
            )
            turn_record["ok"] = True
        except Exception as error:
            turn_record["error"] = f"{type(error).__name__}: {error}"
        turn_record["finished_at"] = now()
        turns.append(turn_record)
        commands.append(turn_record)

        if turn_record["ok"] is not True:
            error_text = str(turn_record.get("error", ""))
            if not any(marker in error_text for marker in RECOVERABLE_TURN_ERRORS):
                status = "stopped_on_error"
                break
        elif selected_step in {"death-terminal", "strategy-review"}:
            status = "episode_complete"
            break

    return {
        "requested_turns": turn_count,
        "completed_turns": len(turns),
        "status": status,
        "all_turns_ok": all(row.get("ok") is True for row in turns),
        "turns": turns,
    }
