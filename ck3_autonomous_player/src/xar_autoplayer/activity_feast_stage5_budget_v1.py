"""Observed peaceful budget for one exclusive private feast Start trial."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .activity_feast_stage5_value_policy import RESOURCE_KEYS
from .construction_formal_consumer import read_construction_ledger
from .faction_gift_pending_v1 import read_faction_gift_ledger_v1
from .family_marriage_formal_consumer import read_family_marriage_ledger
from .player_child_matrilineal_formal_consumer import read_child_matrilineal_ledger


# Reuse the existing independent construction policy's 200-gold cash floor.
PEACEFUL_GOLD_FLOOR_RAW = 20_000_000


def observe_feast_start_budget_v1(
    snapshot: Mapping[str, object], inputs: Mapping[str, object], *,
    state_dir: Path,
) -> dict[str, object]:
    """Bind native war count and durable spending intents to the Start frame.

    This bounded activity lane owns the only submission in its paused frame.
    Stage 1 Confirm and Stage 2 destination selection do not spend resources.
    With no unresolved spending intents, existing same-frame reservations are
    therefore zero. An active war retains an unknown cash reserve and cannot
    finance a positive-Gold feast until the war budget is observed.
    """
    actor = snapshot.get("played_character")
    if (not isinstance(state_dir, Path)
            or snapshot.get("paused") is not True
            or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping)
            or actor.get("character_id") != inputs.get("actor_character_id")
            or snapshot.get("native_revision") != inputs.get("snapshot_revision")
            or snapshot.get("date_raw") != inputs.get("date_raw")
            or snapshot.get("snapshot_id") != inputs.get("post_snapshot_id")
            or snapshot.get("revision") != inputs.get("queried_revision")):
        return {"status": "unavailable", "reason": "budget_frame_unobserved",
                "budget": None}
    wars = snapshot.get("active_wars")
    if (not isinstance(wars, list)
            or any(not isinstance(row, Mapping)
                   or type(row.get("war_id")) is not int
                   or row["war_id"] <= 0 for row in wars)):
        return {"status": "unavailable", "reason": "active_wars_unobserved",
                "budget": None}
    if ("pending_character_interaction" not in snapshot
            or snapshot["pending_character_interaction"] is not None):
        return {"status": "unavailable", "reason": "interaction_pending_or_unobserved",
                "budget": None}
    ledgers = (
        ("construction", read_construction_ledger(state_dir)),
        ("faction_gift", read_faction_gift_ledger_v1(state_dir)),
        ("first_heir_marriage", read_family_marriage_ledger(state_dir)),
        ("child_marriage", read_child_matrilineal_ledger(state_dir)),
    )
    for domain, ledger in ledgers:
        if ledger.get("pending") is not None:
            return {"status": "unavailable", "reason": domain + "_pending",
                    "budget": None}
    return {
        "status": "observed", "reason": "exclusive_paused_activity_lane",
        "frame": {
            "actor_character_id": inputs["actor_character_id"],
            "native_revision": inputs["snapshot_revision"],
            "date_raw": inputs["date_raw"],
            "snapshot_id": snapshot["snapshot_id"],
        },
        "budget": {
            "reserved_raw": dict.fromkeys(RESOURCE_KEYS, 0),
            "peaceful_spend_allowed": True,
            "gold_floor_raw": PEACEFUL_GOLD_FLOOR_RAW,
            "active_war_count": len(wars),
            "war_cash_reserve_raw": None,
        },
    }
