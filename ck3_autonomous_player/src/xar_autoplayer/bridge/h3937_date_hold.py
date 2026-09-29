"""Frozen Robert H3937 war date hold until its formal inputs are certified.

The episode ID is the binding key.  The source actor, war, army, and date are
audit anchors, not switches that can release the hold after identity drift.
No physical inventory mailbox certificate or accepted war/cash policy exists
yet, so this module has no release path.
"""

from __future__ import annotations

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
    """Keep every date in the exact episode frozen, including drifted frames."""

    return bool(
        isinstance(snapshot, dict)
        and snapshot.get("episode_run_id") == H3937_EPISODE_RUN_ID
    )


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
