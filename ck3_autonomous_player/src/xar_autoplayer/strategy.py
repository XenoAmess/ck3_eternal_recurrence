"""Persistent one-life episode summaries used by the gameplay policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .environment import write_json_atomic
from .errors import AgentError
from .runtime import utc_now


ONE_LIFE_STRATEGY_RELATIVE_PATH = Path("strategy") / "one-life-history.json"


def _effective_command(row: dict[str, object]) -> str | None:
    command = row.get("command")
    if command != "auto-turn":
        return command if isinstance(command, str) else None
    result = row.get("result")
    if not isinstance(result, dict):
        return None
    auto_turn = result.get("auto_turn")
    if not isinstance(auto_turn, dict):
        return None
    selected = auto_turn.get("selected_step")
    return selected if isinstance(selected, str) else None


def _latest_index(
    commands: list[dict[str, object]],
    command: str,
    *,
    successful_only: bool = True,
) -> int:
    for fallback_index, row in reversed(tuple(enumerate(commands, start=1))):
        if _effective_command(row) != command:
            continue
        if successful_only and row.get("ok") is not True:
            continue
        raw_index = row.get("index")
        return raw_index if isinstance(raw_index, int) else fallback_index
    return 0


def _latest_effective_result(
    commands: list[dict[str, object]], command: str
) -> dict[str, object] | None:
    for row in reversed(commands):
        if _effective_command(row) != command or row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def choose_one_life_turn(
    commands: list[dict[str, object]],
) -> dict[str, object]:
    """Choose one useful, inspectable action for the current life.

    This is deliberately a one-step planner.  The caller records the result,
    then invokes it again; failures and newly visible events therefore change
    the next choice instead of being hidden inside a long macro.
    """
    rows = [row for row in commands if isinstance(row, dict)]
    last = rows[-1] if rows else None
    last_error = str(last.get("error", "")) if last is not None else ""
    if "one-life death terminal visible:" in last_error:
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal_visible",
            "selected_step": "death-terminal",
            "reason": "player death is visibly stable; settle and end this episode",
        }
    if "ordinary event interrupted" in last_error:
        return {
            "policy": "one-life-turn-v1",
            "phase": "visible_interruption",
            "selected_step": "resolve-current-event",
            "reason": "the previous timeline step stopped on a visible CK3 event",
        }

    if _latest_index(rows, "death-terminal"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal",
            "selected_step": "strategy-review",
            "reason": "player death already ended this one-life episode",
        }

    if not _latest_index(rows, "save-checkpoint"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "baseline",
            "selected_step": "save-checkpoint",
            "reason": "create a native CK3 recovery point before strategic mutations",
        }
    if not _latest_index(rows, "dynasty-review"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_family",
            "selected_step": "dynasty-review",
            "reason": "read the current ruler's spouse, children and available family",
        }
    if not _latest_index(rows, "succession-review"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_domain",
            "selected_step": "succession-review",
            "reason": "measure title loss that matters while the current ruler is alive",
        }

    if not _latest_index(rows, "marriage-confirm-response"):
        marriage_review_index = _latest_index(rows, "marriage-review")
        marriage_alliance_index = _latest_index(rows, "marriage-alliance")
        if not marriage_review_index:
            step = "marriage-review"
            reason = "compare visible child marriage candidates for a current-life alliance"
        elif not marriage_alliance_index:
            step = "marriage-alliance"
            reason = "send the best visible current-life alliance proposal"
        else:
            confirmation_attempt = _latest_index(
                rows, "marriage-confirm-response", successful_only=False
            )
            elapsed_after_attempt = max(
                _latest_index(rows, "war-advance-week"),
                _latest_index(rows, "resolve-current-event"),
                _latest_index(rows, "life-advance"),
                _latest_index(rows, "economic-event-cycle"),
            )
            if not confirmation_attempt or elapsed_after_attempt > confirmation_attempt:
                step = "marriage-confirm-response"
                reason = "check and accept the pending visible betrothal response"
            else:
                step = "war-advance-week"
                reason = "advance one bounded week so the pending proposal can resolve"
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_marriage",
            "selected_step": step,
            "reason": reason,
        }

    victory_index = _latest_index(rows, "war-enforce-demands")
    if not victory_index:
        if not _latest_index(rows, "war-declare-palermo"):
            step = "war-declare-palermo"
            reason = "start the proven low-cost Palermo expansion"
        elif not _latest_index(rows, "war-raise-all"):
            step = "war-raise-all"
            reason = "raise the army for the active Palermo war"
        elif not _latest_index(rows, "war-siege-palermo"):
            step = "war-siege-palermo"
            reason = "move the selected army to the visibly confirmed Palermo fort"
        else:
            latest_status_index = _latest_index(rows, "war-status")
            latest_advance_index = max(
                _latest_index(rows, "war-advance-week"),
                _latest_index(rows, "war-advance-month"),
            )
            status = _latest_effective_result(rows, "war-status")
            war_status = status.get("war_status") if isinstance(status, dict) else None
            score = (
                war_status.get("war_score_percent")
                if isinstance(war_status, dict)
                else None
            )
            if latest_status_index <= latest_advance_index:
                step = "war-status"
                reason = "re-read visible war score after the latest campaign advance"
            elif isinstance(score, int) and score >= 100:
                step = "war-enforce-demands"
                reason = "visible war score reached 100 percent"
            else:
                step = "war-advance-week"
                reason = "continue the active siege for one bounded week"
        return {
            "policy": "one-life-turn-v1",
            "phase": "palermo_war",
            "selected_step": step,
            "reason": reason,
        }

    disband_index = _latest_index(rows, "war-disband-armies")
    if not disband_index or disband_index < victory_index:
        return {
            "policy": "one-life-turn-v1",
            "phase": "postwar",
            "selected_step": "war-disband-armies",
            "reason": "remove raised-army costs after the confirmed victory",
        }

    checkpoint_index = _latest_index(rows, "save-checkpoint")
    strategic_change_index = max(
        victory_index,
        disband_index,
        _latest_index(rows, "marriage-confirm-response"),
    )
    if checkpoint_index < strategic_change_index:
        return {
            "policy": "one-life-turn-v1",
            "phase": "post_milestone_checkpoint",
            "selected_step": "save-checkpoint",
            "reason": "persist the completed war and alliance milestones in a native save",
        }

    cycles_since_checkpoint = sum(
        1
        for row in rows
        if row.get("ok") is True
        and _effective_command(row) in {"life-advance", "economic-event-cycle"}
        and (
            not isinstance(row.get("index"), int)
            or int(row["index"]) > checkpoint_index
        )
    )
    if cycles_since_checkpoint >= 3:
        step = "save-checkpoint"
        reason = "three completed event cycles have elapsed since the last native save"
        phase = "periodic_checkpoint"
    else:
        step = "life-advance"
        reason = "advance the current life to the next visible event and reassess the realm"
        phase = "current_life_loop"
    return {
        "policy": "one-life-turn-v1",
        "phase": phase,
        "selected_step": step,
        "reason": reason,
    }


def _successful_result(
    commands: Iterable[dict[str, object]], command: str
) -> dict[str, object] | None:
    for row in reversed(tuple(commands)):
        if row.get("command") != command or row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _next_run_plan(achievements: dict[str, bool]) -> dict[str, object]:
    priorities: list[dict[str, object]] = []
    if achievements["palermo_holy_war_won"]:
        priorities.append(
            {
                "priority": 100,
                "action": "repeat_palermo_opening_war_when_visible_conditions_match",
                "reason": "the previous life converted the Palermo holy war into a confirmed win",
            }
        )
    else:
        priorities.append(
            {
                "priority": 100,
                "action": "reassess_first_low_cost_expansion",
                "reason": "the previous life did not prove a completed Palermo victory",
            }
        )
    if achievements["danish_betrothal_accepted"]:
        priorities.append(
            {
                "priority": 80,
                "action": "repeat_high_value_child_alliance_review",
                "reason": "the previous life secured the visible Danish betrothal",
            }
        )
    else:
        priorities.append(
            {
                "priority": 80,
                "action": "seek_current_life_marriage_alliance",
                "reason": "the previous life has no confirmed alliance marriage",
            }
        )
    if achievements["partition_risk_visible"]:
        priorities.append(
            {
                "priority": 60,
                "action": "reduce_current_ruler_partition_loss",
                "reason": "succession review exposed title loss during the current life",
            }
        )
    priorities.append(
        {
            "priority": 10,
            "action": "finish_on_player_death_and_record_score",
            "reason": "this is a one-generation roguelike; death ends the episode",
        }
    )
    return {
        "policy": "one-life-visible-outcomes-v1",
        "continue_as_heir_after_death": False,
        "priorities": priorities,
    }


def read_one_life_strategy(state_dir: Path) -> dict[str, object]:
    """Read the cross-run strategy without consulting CK3's protected store."""
    path = state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH
    if not path.exists():
        empty_achievements = {
            "palermo_holy_war_won": False,
            "armies_disbanded": False,
            "danish_betrothal_accepted": False,
            "partition_risk_visible": False,
        }
        return {
            "format_version": 1,
            "mode": "one_life_roguelike",
            "continue_as_heir_after_death": False,
            "episodes": [],
            "next_run_plan": _next_run_plan(empty_achievements),
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentError(f"one-life strategy history is unreadable: {error}") from error
    if (
        not isinstance(payload, dict)
        or payload.get("format_version") != 1
        or payload.get("mode") != "one_life_roguelike"
        or payload.get("continue_as_heir_after_death") is not False
        or not isinstance(payload.get("episodes"), list)
        or not isinstance(payload.get("next_run_plan"), dict)
    ):
        raise AgentError("one-life strategy history has an unsupported contract")
    result = dict(payload)
    result["path"] = str(path)
    return result


def record_one_life_episode(
    state_dir: Path,
    *,
    run_id: str,
    commands: list[dict[str, object]],
    terminal: dict[str, object],
) -> dict[str, object]:
    """Record one finished life and derive the priorities for the next one."""
    if not run_id or terminal.get("terminal") is not True:
        raise AgentError("one-life episode requires a terminal death result")
    succession = _successful_result(commands, "succession-review")
    marriage = _successful_result(commands, "marriage-confirm-response")
    war = _successful_result(commands, "war-enforce-demands")
    disband = _successful_result(commands, "war-disband-armies")
    checkpoint_result = _successful_result(commands, "save-checkpoint")
    achievements = {
        "palermo_holy_war_won": bool(
            isinstance(war, dict)
            and isinstance(war.get("war_victory"), dict)
            and war["war_victory"].get("status") == "victory_enforced"
        ),
        "armies_disbanded": bool(
            isinstance(disband, dict)
            and isinstance(disband.get("army_disband"), dict)
            and disband["army_disband"].get("status") == "disbanded"
        ),
        "danish_betrothal_accepted": bool(
            isinstance(marriage, dict)
            and isinstance(marriage.get("marriage_result"), dict)
            and marriage["marriage_result"].get("status")
            == "accepted_betrothal"
        ),
        "partition_risk_visible": bool(
            isinstance(succession, dict)
            and isinstance(succession.get("succession_state"), dict)
            and succession["succession_state"].get("partition_risk_visible")
            is True
        ),
    }
    checkpoint = None
    if isinstance(checkpoint_result, dict) and isinstance(
        checkpoint_result.get("checkpoint"), dict
    ):
        raw = checkpoint_result["checkpoint"]
        checkpoint = {
            key: raw.get(key) for key in ("name", "size", "sha256")
        }
    episode = {
        "run_id": run_id,
        "finished_at": utc_now(),
        "terminal_reason": "player_death",
        "continue_as_heir_after_death": False,
        "technical_settlement_handoff": bool(
            terminal.get("technical_settlement_handoff")
        ),
        "heir_gameplay_actions": 0,
        "score": terminal.get("score"),
        "achievements": achievements,
        "latest_checkpoint": checkpoint,
        "successful_steps": [
            row.get("command")
            for row in commands
            if row.get("ok") is True and isinstance(row.get("command"), str)
        ],
    }
    history = read_one_life_strategy(state_dir)
    episodes = [
        row
        for row in history["episodes"]
        if isinstance(row, dict) and row.get("run_id") != run_id
    ]
    episodes.append(episode)
    payload = {
        "format_version": 1,
        "mode": "one_life_roguelike",
        "continue_as_heir_after_death": False,
        "updated_at": utc_now(),
        "episodes": episodes,
        "next_run_plan": _next_run_plan(achievements),
    }
    path = state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, payload)
    result = dict(payload)
    result["path"] = str(path)
    result["recorded_episode"] = episode
    return result
