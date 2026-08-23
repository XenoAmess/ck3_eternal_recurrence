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
)
from .bridge.war_contract import (
    RAISE_TROOPS_STEP,
    controllable_armies,
    disband_army_step,
    enforce_demands_step,
    enemy_armies_from_wars,
    move_army_step,
)
from .environment import write_json_atomic
from .errors import AgentError
from .runtime import utc_now


ONE_LIFE_STRATEGY_RELATIVE_PATH = Path("strategy") / "one-life-history.json"
_EMPTY_MARRIAGE_QUERY_LIMIT = 3
_SUBMITTED_MARRIAGE_QUERY_LIMIT = 7


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


def choose_one_life_turn(
    commands: list[dict[str, object]],
    *,
    snapshot: dict[str, object] | None = None,
    action_steps: Iterable[str] | None = None,
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

        enemy = _stable_strongest_army(enemy_armies_from_wars(active_wars))
        pursuit_army = _stable_strongest_army(controlled_armies)
        target_province_id = (
            enemy.get("current_province_id")
            if isinstance(enemy, dict)
            else None
        )
        if isinstance(pursuit_army, dict) and isinstance(target_province_id, int):
            army_id = pursuit_army.get("army_id")
            if isinstance(army_id, int):
                step = move_army_step(army_id, target_province_id)
                pursuit = {
                    "army_id": army_id,
                    "target_army_id": enemy.get("army_id"),
                    "target_province_id": target_province_id,
                    "target_soldiers": enemy.get("soldiers"),
                }
                if _unadvanced_move_submission(rows, step):
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": "the unobservable native move was accepted; advance time before issuing another pursuit order",
                            "pursuit": pursuit,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the native move was accepted but this backend cannot advance the march",
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
                            "reason": "the native army is already at or moving toward the strongest visible enemy; advance the battle",
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
                        "reason": "move the strongest controllable army to the strongest visible enemy army",
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
    successful_marriage_index = _latest_prefix_index(
        rows, "arrange-marriage-"
    )
    if (
        not native_relationship_present
        and (native_relationship_known or not successful_marriage_index)
    ):
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
                    "reason": "submit the first currently valid native marriage choice for this one-life ruler",
                    "marriage_choice": choice,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "the selected native marriage choice is not executable",
                "marriage_choice": choice,
            }
        marriage_query_index = _latest_index(
            rows, QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        )
        marriage_attempt_index = _latest_prefix_index(
            rows, "arrange-marriage-", successful_only=False
        )
        life_advance_index = _latest_index(rows, "life-advance")
        marriage_query_attempts = sum(
            1
            for fallback_index, row in enumerate(rows, start=1)
            if _effective_command(row) == QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
            and row.get("ok") is True
            and (
                row.get("index")
                if isinstance(row.get("index"), int)
                else fallback_index
            )
            > successful_marriage_index
        )
        marriage_query_limit = (
            _SUBMITTED_MARRIAGE_QUERY_LIMIT
            if successful_marriage_index
            else _EMPTY_MARRIAGE_QUERY_LIMIT
        )
        if (
            successful_marriage_index
            > max(marriage_query_index, life_advance_index)
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_response_wait",
                "selected_step": "life-advance",
                "reason": "advance once so CK3 can resolve the submitted marriage proposal",
            }
        if (
            marriage_query_attempts < marriage_query_limit
            and QUERY_ARRANGE_MARRIAGE_CHOICES_STEP in available_steps
            and (
                marriage_query_index == 0
                or (
                    marriage_attempt_index > marriage_query_index
                    and marriage_attempt_index > successful_marriage_index
                )
                or life_advance_index > marriage_query_index
            )
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_discovery",
                "selected_step": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "reason": (
                    "refresh native marriage choices after the world changed or a prior choice failed"
                    if marriage_query_index
                    else "enumerate valid native marriage choices before starting the first war"
                ),
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


def _unadvanced_move_submission(
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
            and action.get("status")
            in {"move_submitted", "move_deferred"}
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
