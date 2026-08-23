"""Persistent one-life episode summaries used by the gameplay policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .bridge.event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
)
from .bridge.declaration_contract import (
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
)
from .bridge.marriage_contract import (
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
    observed_marriage_status,
    parse_arrange_marriage_step,
)
from .bridge.settlement_contract import ONE_LIFE_SETTLEMENT_CAPABILITY
from .bridge.war_contract import (
    RAISE_TROOPS_STEP,
    controllable_armies,
    disband_army_step,
    enemy_primary_default_raise_province_ids,
    enforce_demands_step,
    enemy_armies_from_wars,
    move_army_step,
    parse_move_army_step,
)
from .environment import write_json_atomic
from .errors import AgentError
from .runtime import utc_now


ONE_LIFE_STRATEGY_RELATIVE_PATH = Path("strategy") / "one-life-history.json"
_EMPTY_MARRIAGE_QUERY_LIMIT = 3
_MARRIAGE_RETRY_QUERY_LIMIT = 3
_MARRIAGE_PROPOSAL_MAX_ADVANCES = 7
_MARRIAGE_PROPOSAL_MAX_GAME_DAYS = 30
_NATIVE_MOVE_INTENT_MAX_GAME_DAYS = 90


def _expanded_command_rows(
    commands: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Flatten bounded auto-runs into the same history used by one-step turns."""
    expanded: list[dict[str, object]] = []
    for row in commands:
        if not isinstance(row, dict):
            continue
        command = row.get("command")
        if isinstance(command, str) and (
            command == "auto-run"
            or (
                command.startswith("auto-run ")
                and command.removeprefix("auto-run ").isdigit()
            )
        ):
            result = row.get("result")
            turns = result.get("turns") if isinstance(result, dict) else None
            if isinstance(turns, list):
                for turn in turns:
                    if isinstance(turn, dict):
                        expanded.append({**turn, "index": len(expanded) + 1})
                continue
        expanded.append({**row, "index": len(expanded) + 1})
    return expanded


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


def _latest_prefix_index(
    rows: list[dict[str, object]], prefix: str, *, successful_only: bool = True
) -> int:
    for fallback_index, row in reversed(tuple(enumerate(rows, start=1))):
        command = _effective_command(row)
        if (
            isinstance(command, str)
            and command.startswith(prefix)
            and (not successful_only or row.get("ok") is True)
        ):
            raw_index = row.get("index")
            return raw_index if isinstance(raw_index, int) else fallback_index
    return 0


def _preferred_native_declaration(
    declarations: object,
) -> dict[str, object] | None:
    if not isinstance(declarations, list):
        return None
    rows = [row for row in declarations if isinstance(row, dict)]
    if not rows:
        return None

    def preference(row: dict[str, object]) -> tuple[object, ...]:
        def stable_integer(name: str) -> int:
            value = row.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) else 2**31 - 1

        key = str(row.get("casus_belli_key") or "").casefold()
        if "holy_war" in key and "county" in key:
            key_rank = 0
        elif "county" in key:
            key_rank = 1
        elif "claim" in key:
            key_rank = 2
        else:
            key_rank = 3
        titles = row.get("target_title_ids")
        title_count = len(titles) if isinstance(titles, list) else 1_000_000
        return (
            key_rank,
            title_count,
            stable_integer("target_character_id"),
            stable_integer("casus_belli_index"),
            stable_integer("configuration_index"),
        )

    return min(rows, key=preference)


def _cross_run_focus(plan: dict[str, object] | None) -> str | None:
    """Map the highest cross-run priority to one opening strategy family."""
    priorities = plan.get("priorities") if isinstance(plan, dict) else None
    if not isinstance(priorities, list):
        return None
    ranked = sorted(
        (row for row in priorities if isinstance(row, dict)),
        key=lambda row: (
            -int(row.get("priority", 0))
            if isinstance(row.get("priority"), int)
            and not isinstance(row.get("priority"), bool)
            else 0,
            str(row.get("action") or ""),
        ),
    )
    for row in ranked:
        action = str(row.get("action") or "").casefold()
        if any(token in action for token in ("war", "expansion", "palermo")):
            return "war"
        if any(token in action for token in ("marriage", "alliance", "betrothal")):
            return "marriage"
        if any(token in action for token in ("succession", "partition")):
            return "succession"
    return None


def _native_marriage_attempt_state(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Recover the latest outbound proposal intent from persistent history."""
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        choice_id = parse_arrange_marriage_step(_effective_command(row))
        if choice_id is None:
            continue
        parsed_played, parsed_candidate = (
            int(value) for value in choice_id.split("-", maxsplit=1)
        )
        row_index = (
            row.get("index")
            if isinstance(row.get("index"), int)
            else position + 1
        )
        if row.get("ok") is not True:
            return {
                "status": "retry",
                "reason": "submission_failed",
                "played_character_id": parsed_played,
                "candidate_character_id": parsed_candidate,
                "attempt_index": row_index,
                "retry_index": row_index,
            }
        result = row.get("result")
        action = (
            result.get("marriage_action")
            if isinstance(result, dict)
            else None
        )
        if not isinstance(action, dict):
            return {
                "status": "retry",
                "reason": "submission_result_missing",
                "played_character_id": parsed_played,
                "candidate_character_id": parsed_candidate,
                "attempt_index": row_index,
                "retry_index": row_index,
            }
        played_character_id = action.get("played_character_id")
        candidate_character_id = action.get("candidate_character_id")
        if isinstance(played_character_id, bool) or not isinstance(
            played_character_id, int
        ):
            played_character_id = parsed_played
        if isinstance(candidate_character_id, bool) or not isinstance(
            candidate_character_id, int
        ):
            candidate_character_id = parsed_candidate
        if action.get("status") != "proposal_submitted":
            return {
                "status": "retry",
                "reason": "submission_rejected",
                "played_character_id": played_character_id,
                "candidate_character_id": candidate_character_id,
                "attempt_index": row_index,
                "retry_index": row_index,
            }

        relationship_status = observed_marriage_status(
            snapshot.get("played_character"),
            played_character_id=played_character_id,
            candidate_character_id=candidate_character_id,
        )
        recorded_outcome = result.get("marriage_result")
        if relationship_status is not None or (
            isinstance(recorded_outcome, dict)
            and recorded_outcome.get("source")
            == "native_relationship_snapshot"
            and recorded_outcome.get("candidate_character_id")
            == candidate_character_id
            and recorded_outcome.get("status")
            in {"accepted_betrothal", "accepted_marriage"}
        ):
            return {
                "status": "completed",
                "relationship_status": (
                    relationship_status
                    if relationship_status is not None
                    else recorded_outcome.get("status")
                ),
                "played_character_id": played_character_id,
                "candidate_character_id": candidate_character_id,
                "attempt_index": row_index,
            }

        submitted_date_raw = action.get("submitted_date_raw")
        current_date_raw = snapshot.get("date_raw")
        elapsed_days: int | None = None
        if (
            isinstance(submitted_date_raw, int)
            and not isinstance(submitted_date_raw, bool)
            and isinstance(current_date_raw, int)
            and not isinstance(current_date_raw, bool)
            and current_date_raw >= submitted_date_raw
        ):
            elapsed_days = (current_date_raw - submitted_date_raw) // 24
        advances = sum(
            1
            for later in commands[position + 1 :]
            if _effective_command(later) == "life-advance"
            and later.get("ok") is True
        )
        timed_out = (
            advances >= _MARRIAGE_PROPOSAL_MAX_ADVANCES
            or (
                elapsed_days is not None
                and elapsed_days >= _MARRIAGE_PROPOSAL_MAX_GAME_DAYS
            )
        )
        return {
            "status": "retry" if timed_out else "pending",
            "reason": "proposal_timeout" if timed_out else "awaiting_relationship",
            "played_character_id": played_character_id,
            "candidate_character_id": candidate_character_id,
            "submitted_date_raw": (
                submitted_date_raw
                if isinstance(submitted_date_raw, int)
                and not isinstance(submitted_date_raw, bool)
                else None
            ),
            "elapsed_days": elapsed_days,
            "life_advances": advances,
            "timeout_days": _MARRIAGE_PROPOSAL_MAX_GAME_DAYS,
            "max_life_advances": _MARRIAGE_PROPOSAL_MAX_ADVANCES,
            "attempt_index": row_index,
            "retry_index": row_index,
        }
    return None


def choose_one_life_turn(
    commands: list[dict[str, object]],
    *,
    snapshot: dict[str, object] | None = None,
    action_steps: Iterable[str] | None = None,
    next_run_plan: dict[str, object] | None = None,
) -> dict[str, object]:
    """Choose one useful, inspectable action for the current life.

    This is deliberately a one-step planner.  The caller records the result,
    then invokes it again; failures and newly visible events therefore change
    the next choice instead of being hidden inside a long macro.
    """
    rows = _expanded_command_rows(commands)
    available_steps = {
        step for step in (action_steps or ()) if isinstance(step, str) and step
    }
    cross_run_focus = _cross_run_focus(next_run_plan)
    played_character = (
        snapshot.get("played_character")
        if isinstance(snapshot, dict)
        else None
    )
    terminal_reason = (
        snapshot.get("one_life_terminal_reason")
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("one_life_terminal_reason"), str)
        else (
            "played_character_dead"
            if isinstance(played_character, dict)
            and played_character.get("alive") is False
            else None
        )
    )
    if terminal_reason is not None:
        episode_character_id = (
            snapshot.get("episode_character_id")
            if isinstance(snapshot, dict)
            else None
        )
        completed_terminal = _latest_effective_result(rows, "death-terminal")
        if (
            isinstance(completed_terminal, dict)
            and completed_terminal.get("terminal") is True
            and completed_terminal.get("score") is not None
            and completed_terminal.get("settlement_status")
            in {None, "complete"}
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_complete",
                "selected_step": (
                    "start-next-episode"
                    if "start-next-episode" in available_steps
                    else None
                ),
                "reason": "this one-life episode is already settled",
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "score": completed_terminal.get("score"),
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
            }
        if (
            isinstance(completed_terminal, dict)
            and completed_terminal.get("settlement_status")
            == "settlement_unavailable"
            and isinstance(snapshot, dict)
            and snapshot.get("one_life_settlement_status")
            == "settlement_unavailable"
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_settlement_unavailable",
                "selected_step": None,
                "required_capability": (
                    ONE_LIFE_SETTLEMENT_CAPABILITY
                ),
                "reason": (
                    "the episode is terminal but this bridge cannot publish "
                    "its score; wait for a settlement-capable backend"
                ),
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
            }
        reason = (
            "CK3 changed the played CharacterID after the episode character; "
            "end this one-life episode instead of continuing as the heir"
            if terminal_reason == "played_character_changed"
            else "the native played character is dead; end this one-life episode"
        )
        if "death-terminal" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_native",
                "selected_step": "death-terminal",
                "reason": reason,
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "played_character": (
                    dict(played_character)
                    if isinstance(played_character, dict)
                    else None
                ),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal_native_unsupported",
            "selected_step": None,
            "required_step": "death-terminal",
            "reason": "the backend cannot finalize the detected player death",
            "terminal_reason": terminal_reason,
            "episode_character_id": episode_character_id,
            "played_character": (
                dict(played_character)
                if isinstance(played_character, dict)
                else None
            ),
        }
    raw_active_event = (
        snapshot.get("active_event", snapshot.get("current_event"))
        if isinstance(snapshot, dict)
        else None
    )
    active_event = normalize_active_event(
        raw_active_event,
        default_source=(
            str(snapshot.get("source"))
            if isinstance(snapshot, dict) and snapshot.get("source")
            else "planner"
        ),
    )
    if active_event is not None:
        option_number = choose_event_option_number(active_event)
        exact_step = (
            event_option_step(option_number)
            if option_number is not None
            else None
        )
        event_summary = {
            "instance_id": active_event.get("instance_id"),
            "option_count": active_event.get("option_count"),
            "selected_option_number": option_number,
            "selected_option_index": (
                option_number - 1 if option_number is not None else None
            ),
        }
        if exact_step is not None and exact_step in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "active_event",
                "selected_step": exact_step,
                "reason": "select the best enabled option on the active CK3 event",
                "active_event": event_summary,
            }
        if "resolve-current-event" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "active_event_visual_fallback",
                "selected_step": "resolve-current-event",
                "reason": (
                    "the active event is delegated explicitly to the visual "
                    "event resolver"
                ),
                "active_event": event_summary,
            }
        required_step = exact_step or "resolve-current-event"
        return {
            "policy": "one-life-turn-v1",
            "phase": "active_event_unsupported",
            "selected_step": None,
            "required_step": required_step,
            "reason": (
                "the selected backend reported an active event but did not "
                f"advertise {required_step}"
            ),
            "active_event": event_summary,
        }

    pending_interaction = (
        snapshot.get("pending_character_interaction")
        if isinstance(snapshot, dict)
        else None
    )
    if (
        isinstance(pending_interaction, dict)
        and pending_interaction.get("auto_accept_notification") is False
    ):
        step = "accept-pending-character-interaction"
        summary = {
            "instance_id": pending_interaction.get("instance_id"),
            "sender_character_id": pending_interaction.get(
                "sender_character_id"
            ),
        }
        if step in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "pending_character_interaction",
                "selected_step": step,
                "reason": "accept the current native character interaction",
                "pending_character_interaction": summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "pending_character_interaction_unsupported",
            "selected_step": None,
            "required_step": step,
            "reason": "the backend cannot reply to the pending character interaction",
            "pending_character_interaction": summary,
        }

    active_wars = (
        [war for war in snapshot.get("active_wars", []) if isinstance(war, dict)]
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("active_wars"), list)
        else []
    )
    player_armies = (
        [army for army in snapshot.get("player_armies", []) if isinstance(army, dict)]
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("player_armies"), list)
        else []
    )
    controlled_armies = controllable_armies(player_armies)
    if active_wars:
        war_summary = [
            {
                "war_id": war.get("war_id"),
                "player_side": war.get("player_side"),
                "primary_opponent_character_id": war.get(
                    "primary_opponent_character_id"
                ),
                "player_is_primary_war_leader": war.get(
                    "player_is_primary_war_leader"
                ),
                "enemy_primary_default_raise_province_id": war.get(
                    "enemy_primary_default_raise_province_id"
                ),
                "player_relative_war_score": war.get(
                    "player_relative_war_score"
                ),
            }
            for war in active_wars
        ]
        enforceable = next(
            (
                war
                for war in active_wars
                if isinstance(war.get("war_id"), int)
                and isinstance(war.get("player_relative_war_score"), int)
                and int(war["player_relative_war_score"]) >= 100
                and (
                    war.get("player_is_primary_war_leader") is True
                    or (
                        war.get("player_is_primary_war_leader") is None
                        and enforce_demands_step(int(war["war_id"]))
                        in available_steps
                    )
                )
            ),
            None,
        )
        if isinstance(enforceable, dict):
            step = enforce_demands_step(int(enforceable["war_id"]))
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_enforce_demands",
                    "selected_step": step,
                    "reason": "the native war reached 100%; enforce demands before issuing more army orders",
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_enforce_demands_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "the war reached 100% but this backend cannot enforce demands",
                "active_wars": war_summary,
            }
        if not controlled_armies:
            if RAISE_TROOPS_STEP in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_raise",
                    "selected_step": RAISE_TROOPS_STEP,
                    "reason": "an active war has no controllable army; raise troops at the native default rally point",
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_raise_unsupported",
                "selected_step": None,
                "required_step": RAISE_TROOPS_STEP,
                "reason": "the active war cannot continue until this backend can raise troops",
                "active_wars": war_summary,
            }

        visible_enemies = [
            army
            for army in enemy_armies_from_wars(active_wars)
            if isinstance(army.get("current_province_id"), int)
        ]
        enemy = _stable_strongest_army(visible_enemies)
        pursuit_army = _stable_strongest_army(controlled_armies)
        fallback_province_ids = enemy_primary_default_raise_province_ids(
            active_wars
        )
        siege_objective_province_ids = _attacker_siege_objective_province_ids(
            active_wars
        )
        objective_kind = "pursuit"
        if isinstance(pursuit_army, dict) and siege_objective_province_ids:
            current_province_id = pursuit_army.get("current_province_id")
            local_enemies = [
                army
                for army in visible_enemies
                if isinstance(current_province_id, int)
                and army.get("current_province_id") == current_province_id
            ]
            if local_enemies:
                enemy = _stable_strongest_army(local_enemies)
                target_province_id = current_province_id
                target_source = "enemy_army"
            else:
                enemy = None
                target_province_id = siege_objective_province_ids[0]
                target_source = "enemy_primary_default_raise_province"
                objective_kind = "siege"
        elif isinstance(enemy, dict):
            target_province_id = enemy.get("current_province_id")
            target_source = "enemy_army"
        else:
            target_province_id = (
                fallback_province_ids[0]
                if fallback_province_ids
                else None
            )
            target_source = "enemy_primary_default_raise_province"
        if isinstance(pursuit_army, dict) and isinstance(target_province_id, int):
            army_id = pursuit_army.get("army_id")
            if isinstance(army_id, int):
                step = move_army_step(army_id, target_province_id)
                pursuit = {
                    "army_id": army_id,
                    "target_army_id": (
                        enemy.get("army_id")
                        if isinstance(enemy, dict)
                        else None
                    ),
                    "target_province_id": target_province_id,
                    "target_soldiers": (
                        enemy.get("soldiers")
                        if isinstance(enemy, dict)
                        else None
                    ),
                    "target_source": target_source,
                    "objective_kind": objective_kind,
                }
                active_move_intent = _active_native_move_intent(
                    rows,
                    snapshot if isinstance(snapshot, dict) else {},
                    army_id=army_id,
                    target_province_id=target_province_id,
                )
                if active_move_intent is not None:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": "the accepted native move intent is still active; advance the war without submitting the same move again",
                            "pursuit": pursuit,
                            "move_intent": active_move_intent,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the native move intent is still active but this backend cannot advance the march",
                        "pursuit": pursuit,
                        "move_intent": active_move_intent,
                        "active_wars": war_summary,
                    }
                if _unadvanced_deferred_move(rows, step):
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": "the army was not move-ready; advance once before retrying the order",
                            "pursuit": pursuit,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the deferred native move needs time to advance but this backend cannot do so",
                        "pursuit": pursuit,
                        "active_wars": war_summary,
                    }
                if target_province_id in {
                    pursuit_army.get("current_province_id"),
                    pursuit_army.get("move_target_province_id"),
                }:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": (
                                "the native army is already at or moving toward the stable siege objective; advance the occupation"
                                if objective_kind == "siege"
                                else "the native army is already at or moving toward the strongest visible enemy; advance the battle"
                            ),
                            "pursuit": pursuit,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the army is already pursuing the enemy but this backend cannot advance time",
                        "pursuit": pursuit,
                        "active_wars": war_summary,
                    }
                if step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit",
                        "selected_step": step,
                        "reason": (
                            "move the strongest controllable army to the strongest visible enemy army"
                            if target_source == "enemy_army"
                            else (
                                "positive attacker war score is established; move to the primary opponent's default rally province as a stable siege objective"
                                if objective_kind == "siege"
                                else "no enemy army province is visible; move toward the primary opponent's default rally province fallback"
                            )
                        ),
                        "pursuit": pursuit,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_pursuit_unsupported",
                    "selected_step": None,
                    "required_step": step,
                    "reason": "the backend cannot issue the required native army move",
                    "pursuit": pursuit,
                    "active_wars": war_summary,
                }
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_reconnaissance",
                "selected_step": "life-advance",
                "reason": "no enemy province is currently published; advance one bounded native interval and inspect again",
                "active_wars": war_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_reconnaissance_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": "the active war has no published enemy province and time cannot advance",
            "active_wars": war_summary,
        }

    if controlled_armies:
        army = _stable_strongest_army(controlled_armies)
        army_id = army.get("army_id") if isinstance(army, dict) else None
        if isinstance(army_id, int):
            step = disband_army_step(army_id)
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_postwar_disband",
                    "selected_step": step,
                    "reason": "no active war remains; disband the strongest residual player army",
                    "army_id": army_id,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_postwar_disband_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "a player army remains after the war but this backend cannot disband it",
                "army_id": army_id,
            }

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

    if (
        cross_run_focus == "succession"
        and not _latest_index(rows, "succession-review")
        and "succession-review" in available_steps
    ):
        return {
            "policy": "one-life-turn-v1",
            "phase": "cross_run_succession_first",
            "selected_step": "succession-review",
            "reason": "the previous episode promoted succession review to the first strategic action",
        }

    native_relationship_known = (
        isinstance(played_character, dict)
        and {
            "betrothed_id",
            "primary_spouse_id",
            "spouse_ids",
        }
        <= played_character.keys()
    )
    native_relationship_present = (
        native_relationship_known
        and (
            played_character.get("betrothed_id") is not None
            or played_character.get("primary_spouse_id") is not None
            or bool(played_character.get("spouse_ids"))
        )
    )
    marriage_attempt = _native_marriage_attempt_state(
        rows, snapshot if isinstance(snapshot, dict) else {}
    )
    war_attempted = bool(
        _latest_index(rows, QUERY_DECLARABLE_WARS_STEP)
        or _latest_prefix_index(rows, "declare-war-", successful_only=False)
        or _latest_prefix_index(rows, "enforce-demands-", successful_only=False)
    )
    defer_marriage_for_war = cross_run_focus == "war" and not war_attempted
    if (
        not native_relationship_present
        and (marriage_attempt is not None or not defer_marriage_for_war)
    ):
        if (
            isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "pending"
        ):
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_arrange_marriage_response_wait",
                    "selected_step": "life-advance",
                    "reason": "advance one bounded interval while waiting for the exact spouse or betrothal relationship",
                    "marriage_intent": marriage_attempt,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_response_wait_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the native proposal is unresolved but this backend cannot advance time",
                "marriage_intent": marriage_attempt,
            }

        retry_candidate_id = (
            marriage_attempt.get("candidate_character_id")
            if isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "retry"
            else None
        )
        raw_marriage_choices = (
            snapshot.get("arrange_marriage_choices")
            if isinstance(snapshot, dict)
            else None
        )
        marriage_choices = sorted(
            (
                choice
                for choice in raw_marriage_choices
                if isinstance(choice, dict)
                and isinstance(choice.get("choice_id"), str)
                and isinstance(choice.get("candidate_character_id"), int)
            ),
            key=lambda choice: (
                choice.get("candidate_character_id") == retry_candidate_id,
                int(choice["candidate_character_id"]),
                str(choice["choice_id"]),
            ),
        ) if isinstance(raw_marriage_choices, list) else []
        if marriage_choices:
            choice = marriage_choices[0]
            step = arrange_marriage_step(str(choice["choice_id"]))
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_arrange_marriage",
                    "selected_step": step,
                    "reason": (
                        "submit a fresh valid candidate after the previous proposal failed or timed out"
                        if retry_candidate_id is not None
                        else "submit the first currently valid native marriage choice for this one-life ruler"
                    ),
                    "marriage_choice": choice,
                    "previous_marriage_intent": marriage_attempt,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "the selected native marriage choice is not executable",
                "marriage_choice": choice,
            }
        query_anchor = (
            int(marriage_attempt.get("retry_index", 0))
            if isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "retry"
            else 0
        )
        marriage_query_index = _latest_index(
            rows,
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
            successful_only=False,
        )
        successful_marriage_query_index = _latest_index(
            rows, QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        )
        life_advance_index = _latest_index(rows, "life-advance")
        marriage_query_attempts = sum(
            1
            for fallback_index, row in enumerate(rows, start=1)
            if _effective_command(row) == QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
            and (
                row.get("index")
                if isinstance(row.get("index"), int)
                else fallback_index
            )
            > query_anchor
        )
        marriage_query_limit = (
            _MARRIAGE_RETRY_QUERY_LIMIT
            if query_anchor
            else _EMPTY_MARRIAGE_QUERY_LIMIT
        )
        latest_query_result = _latest_effective_result(
            rows, QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        )
        lost_nonempty_query_cache = (
            successful_marriage_query_index > query_anchor
            and successful_marriage_query_index == marriage_query_index
            and isinstance(latest_query_result, dict)
            and isinstance(
                latest_query_result.get("arrange_marriage_choices"), list
            )
            and bool(latest_query_result["arrange_marriage_choices"])
        )
        if (
            marriage_query_attempts < marriage_query_limit
            and QUERY_ARRANGE_MARRIAGE_CHOICES_STEP in available_steps
            and (
                marriage_query_index <= query_anchor
                or successful_marriage_query_index != marriage_query_index
                or life_advance_index > marriage_query_index
                or lost_nonempty_query_cache
            )
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_discovery",
                "selected_step": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "reason": (
                    "rebuild the native choice cache after reconnecting or refresh candidates after a failed proposal"
                    if lost_nonempty_query_cache or query_anchor
                    else "refresh native marriage choices after the world changed"
                    if marriage_query_index
                    else "enumerate valid native marriage choices before starting the first war"
                ),
                "previous_marriage_intent": marriage_attempt,
            }
        if (
            marriage_query_attempts < marriage_query_limit
            and marriage_query_index > life_advance_index
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_refresh",
                "selected_step": "life-advance",
                "reason": "the latest native marriage query was empty; advance time once before refreshing it",
                "previous_marriage_intent": marriage_attempt,
            }

    declaration_index = _latest_prefix_index(rows, "declare-war-")
    life_advance_index = _latest_index(rows, "life-advance")
    if declaration_index > life_advance_index:
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_declaration_progress",
                "selected_step": "life-advance",
                "reason": "the native declaration was submitted; advance once for the war state to materialize",
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_declaration_progress_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": "the native declaration was submitted but this backend cannot advance the map",
        }

    declaration = _preferred_native_declaration(
        snapshot.get("declarable_wars") if isinstance(snapshot, dict) else None
    )
    if isinstance(declaration, dict):
        declaration_id = declaration.get("declaration_id")
        if isinstance(declaration_id, str):
            step = declare_war_step(declaration_id)
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_declaration",
                    "selected_step": step,
                    "reason": "declare the best currently enumerated native county-scale war",
                    "declaration": declaration,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_declaration_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "the selected native war declaration is not executable",
                "declaration": declaration,
            }

    if QUERY_DECLARABLE_WARS_STEP in available_steps:
        query_index = _latest_index(rows, QUERY_DECLARABLE_WARS_STEP)
        if query_index > life_advance_index and "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_discovery_progress",
                "selected_step": "life-advance",
                "reason": "no war was currently declarable; advance once before the next native query",
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_discovery",
            "selected_step": QUERY_DECLARABLE_WARS_STEP,
            "reason": "enumerate current native war declarations before using visual diplomacy",
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


def _stable_strongest_army(
    armies: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    rows = [army for army in armies if isinstance(army.get("army_id"), int)]
    if not rows:
        return None
    return max(
        rows,
        key=lambda army: (
            army.get("soldiers")
            if isinstance(army.get("soldiers"), int)
            else -1,
            -int(army["army_id"]),
        ),
    )


def _attacker_siege_objective_province_ids(
    wars: Iterable[dict[str, object]],
) -> list[int]:
    """Choose stable siege anchors only after an attacker earns war score."""
    province_ids: set[int] = set()
    for war in wars:
        score = war.get("player_relative_war_score")
        province_id = war.get("enemy_primary_default_raise_province_id")
        if (
            war.get("player_side") == "attacker"
            and war.get("player_is_primary_war_leader") is True
            and isinstance(score, int)
            and not isinstance(score, bool)
            and score > 0
            and isinstance(province_id, int)
            and not isinstance(province_id, bool)
        ):
            province_ids.add(province_id)
    return sorted(province_ids)


def _active_native_move_intent(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int,
    target_province_id: int,
) -> dict[str, object] | None:
    latest_position = -1
    latest_row: dict[str, object] | None = None
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        command = _effective_command(row)
        if command == "restore-checkpoint" and row.get("ok") is True:
            return None
        parsed = parse_move_army_step(command)
        if parsed is None or parsed[0] != army_id:
            continue
        latest_position = position
        latest_row = row
        break
    if latest_row is None or latest_row.get("ok") is not True:
        return None
    parsed = parse_move_army_step(_effective_command(latest_row))
    if parsed != (army_id, target_province_id):
        return None
    result = latest_row.get("result")
    action = result.get("war_action") if isinstance(result, dict) else None
    if (
        not isinstance(action, dict)
        or action.get("status") not in {"move_submitted", "moving"}
        or result.get("accepted") is False
    ):
        return None
    action_army_id = action.get("army_id")
    action_target_province_id = action.get("target_province_id")
    if (
        action_army_id is not None
        and action_army_id != army_id
    ) or (
        action_target_province_id is not None
        and action_target_province_id != target_province_id
    ):
        return None

    player_armies = snapshot.get("player_armies")
    army = (
        next(
            (
                row
                for row in player_armies
                if isinstance(row, dict) and row.get("army_id") == army_id
            ),
            None,
        )
        if isinstance(player_armies, list)
        else None
    )
    if not isinstance(army, dict):
        return None
    if army.get("current_province_id") == target_province_id:
        return None
    observed_target = army.get("move_target_province_id")
    if isinstance(observed_target, int) and observed_target != target_province_id:
        return None

    elapsed_days = _move_intent_elapsed_days(
        commands,
        latest_position=latest_position,
        action=action,
        snapshot=snapshot,
    )
    if elapsed_days >= _NATIVE_MOVE_INTENT_MAX_GAME_DAYS:
        return None
    return {
        "status": "active",
        "army_id": army_id,
        "target_province_id": target_province_id,
        "elapsed_days": elapsed_days,
        "timeout_days": _NATIVE_MOVE_INTENT_MAX_GAME_DAYS,
    }


def _move_intent_elapsed_days(
    commands: list[dict[str, object]],
    *,
    latest_position: int,
    action: dict[str, object],
    snapshot: dict[str, object],
) -> int:
    submitted_date_raw = action.get("submitted_date_raw")
    current_date_raw = snapshot.get("date_raw")
    if (
        isinstance(submitted_date_raw, int)
        and not isinstance(submitted_date_raw, bool)
        and isinstance(current_date_raw, int)
        and not isinstance(current_date_raw, bool)
        and current_date_raw >= submitted_date_raw
    ):
        return (current_date_raw - submitted_date_raw) // 24

    elapsed_days = 0
    for row in commands[latest_position + 1 :]:
        if _effective_command(row) != "life-advance" or row.get("ok") is not True:
            continue
        result = row.get("result")
        if not isinstance(result, dict):
            continue
        elapsed = result.get("elapsed_days")
        if (
            isinstance(elapsed, int)
            and not isinstance(elapsed, bool)
            and elapsed >= 0
        ):
            elapsed_days += elapsed
            continue
        starting_date_raw = result.get("starting_date_raw")
        ending_date_raw = result.get("ending_date_raw")
        if (
            isinstance(starting_date_raw, int)
            and not isinstance(starting_date_raw, bool)
            and isinstance(ending_date_raw, int)
            and not isinstance(ending_date_raw, bool)
            and ending_date_raw >= starting_date_raw
        ):
            elapsed_days += (ending_date_raw - starting_date_raw) // 24
    return elapsed_days


def _unadvanced_deferred_move(
    commands: list[dict[str, object]], step: str
) -> bool:
    for row in reversed(commands):
        command = _effective_command(row)
        if command == "life-advance" and row.get("ok") is True:
            return False
        if command != step or row.get("ok") is not True:
            continue
        result = row.get("result")
        action = result.get("war_action") if isinstance(result, dict) else None
        return (
            isinstance(action, dict)
            and action.get("status") == "move_deferred"
        )
    return False


def _successful_result(
    commands: Iterable[dict[str, object]], command: str
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        if _effective_command(row) != command or row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _successful_result_for_steps(
    commands: Iterable[dict[str, object]],
    *,
    exact: tuple[str, ...] = (),
    prefixes: tuple[str, ...] = (),
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        command = _effective_command(row)
        if not isinstance(command, str) or (
            command not in exact
            and not any(command.startswith(prefix) for prefix in prefixes)
        ):
            continue
        if row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _accepted_marriage_result(
    commands: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        command = _effective_command(row)
        if row.get("ok") is not True or not isinstance(command, str):
            continue
        result = row.get("result")
        outcome = (
            result.get("marriage_result")
            if isinstance(result, dict)
            else None
        )
        if (
            not isinstance(result, dict)
            or not isinstance(outcome, dict)
            or outcome.get("status")
            not in {"accepted_betrothal", "accepted_marriage"}
        ):
            continue
        if command == "marriage-confirm-response":
            return result
        if (
            parse_arrange_marriage_step(command) is not None
            and outcome.get("source") == "native_relationship_snapshot"
            and isinstance(outcome.get("candidate_character_id"), int)
            and not isinstance(outcome.get("candidate_character_id"), bool)
        ):
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
                "priority": 70,
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
                "priority": 100,
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
    marriage = _accepted_marriage_result(commands)
    war = _successful_result_for_steps(
        commands,
        exact=("war-enforce-demands",),
        prefixes=("enforce-demands-",),
    )
    disband = _successful_result_for_steps(
        commands,
        exact=("war-disband-armies",),
        prefixes=("disband-army-",),
    )
    checkpoint_result = _successful_result(commands, "save-checkpoint")
    achievements = {
        "palermo_holy_war_won": bool(
            isinstance(war, dict)
            and isinstance(war.get("war_victory"), dict)
            and war["war_victory"].get("status") == "victory_enforced"
        ),
        "armies_disbanded": bool(
            isinstance(disband, dict)
            and (
                (
                    isinstance(disband.get("army_disband"), dict)
                    and disband["army_disband"].get("status") == "disbanded"
                )
                or (
                    isinstance(disband.get("war_action"), dict)
                    and disband["war_action"].get("status") == "disbanded"
                )
            )
        ),
        "danish_betrothal_accepted": bool(
            isinstance(marriage, dict)
            and isinstance(marriage.get("marriage_result"), dict)
            and marriage["marriage_result"].get("status")
            in {"accepted_betrothal", "accepted_marriage"}
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
        "terminal_reason": (
            terminal.get("terminal_reason")
            if isinstance(terminal.get("terminal_reason"), str)
            else "player_death"
        ),
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
