"""Keep the historical H3937 read-only research episode frozen.

The episode ID binds the old research hold, including identity/date drift.
The ordinary campaign reuses that episode ID after migration; its persisted
typed goal and current actor distinguish normal play from the research run.
"""

from __future__ import annotations

from .active_combat_retreat_contract import ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX
from .succession_transition_contract import ORDINARY_CAMPAIGN_SUCCESSION
from .war_contract import (
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    is_life_advance_step,
)

H3937_EPISODE_RUN_ID = "native-29829-2bc2d599f7f9"
H3937_ACTOR_CHARACTER_ID = 29_829
H3937_WAR_ID = 16_777_231
H3937_ARMY_ID = 83_886_367
H3937_SOURCE_DATE_RAW = 53_219_928


def h3937_date_hold_active(snapshot: object) -> bool:
    """Hold the legacy research profile, not its migrated ordinary campaign."""

    if (
        not isinstance(snapshot, dict)
        or snapshot.get("episode_run_id") != H3937_EPISODE_RUN_ID
    ):
        return False
    lifecycle = snapshot.get("succession_lifecycle")
    goal = snapshot.get("campaign_goal")
    actor = snapshot.get("played_character")
    ordinary_campaign = (
        isinstance(lifecycle, dict)
        and lifecycle.get("lifecycle") == ORDINARY_CAMPAIGN_SUCCESSION
        and isinstance(goal, dict)
        and goal.get("format_version") == 1
        and goal.get("goal_key") == "dynasty_continuity"
        and goal.get("campaign_id") == snapshot["episode_run_id"]
        and isinstance(actor, dict)
        and goal.get("current_character_id") == actor.get("character_id")
    )
    return not ordinary_campaign


def is_date_control_step(step: object) -> bool:
    """Classify formal date composites and raw timeline control literals."""

    return bool(
        is_life_advance_step(step)
        or step == "resume-map"
        or (isinstance(step, str) and step in {
            # These capability templates are advertised without their bound
            # army/war/date payload.  The generic parser only recognizes the
            # concrete form, so classify the templates here as date controls.
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
            "set-speed-1",
            "set-speed-2",
            "set-speed-3",
            "set-speed-4",
            "set-speed-5",
        })
    )


def is_army_move_control_step(step: object) -> bool:
    """Include malformed move literals and the composite that submits a move."""

    return bool(
        isinstance(step, str)
        and (
            step == "move-army"
            or step.startswith("move-army-")
            or step == "order-active-combat-retreat-v1"
            or step.startswith(ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX)
        )
    )


def h3937_date_hold_audit(snapshot: dict[str, object]) -> dict[str, object]:
    """Record exact source anchors without allowing a mismatch to bypass."""

    actor = snapshot.get("played_character")
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    actor_id = actor.get("character_id") if isinstance(actor, dict) else None
    war_present = bool(
        isinstance(wars, list)
        and any(
            isinstance(row, dict) and row.get("war_id") == H3937_WAR_ID
            for row in wars
        )
    )
    army_present = bool(
        isinstance(armies, list)
        and any(
            isinstance(row, dict) and row.get("army_id") == H3937_ARMY_ID
            for row in armies
        )
    )
    return {
        "episode_run_id": H3937_EPISODE_RUN_ID,
        "source_actor_character_id": H3937_ACTOR_CHARACTER_ID,
        "source_war_id": H3937_WAR_ID,
        "source_army_id": H3937_ARMY_ID,
        "source_date_raw": H3937_SOURCE_DATE_RAW,
        "observed_actor_character_id": actor_id,
        "observed_date_raw": snapshot.get("date_raw"),
        "source_actor_matches": actor_id == H3937_ACTOR_CHARACTER_ID,
        "source_war_present": war_present,
        "source_army_present": army_present,
        "source_date_matches": snapshot.get("date_raw") == H3937_SOURCE_DATE_RAW,
    }
