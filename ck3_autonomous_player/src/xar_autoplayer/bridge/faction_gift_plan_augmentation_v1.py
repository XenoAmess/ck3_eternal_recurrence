"""Attach a private read-only faction candidate to one ordinary formal plan.

The service owner may call this after its existing planner has chosen a time
advance. No gift step becomes routable, and no mandatory event/interaction is
reclassified as optional.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Mapping

from .driver import BridgeUnavailableError
from ..faction_gift_pending_v1 import read_faction_gift_ledger_v1


def attach_faction_gift_private_candidate_v1(
    planned: dict[str, object], snapshot: Mapping[str, object],
    root_view: Mapping[str, object] | None, *, state_dir: Path | None,
    query: Callable[..., dict[str, object]] | None,
) -> dict[str, object]:
    """Expose a decision trace within a normal turn; submit remains disabled."""
    plan = planned.get("plan")
    if not isinstance(plan, dict) or plan.get("selected_step") != "life-advance":
        return planned
    if not isinstance(root_view, Mapping):
        return planned
    status = root_view.get("status")
    if status == "known_empty":
        plan["faction_gift_private_candidate_v1"] = {
            "status": "known_empty", "gift_submission_enabled": False,
            "public_capability_advertised": False,
            "faction_dissolved_or_gift_applied": "not_inferred",
        }
        return planned
    if status != "targeting_present":
        return planned
    if state_dir is None:
        plan["faction_gift_private_candidate_v1"] = {
            "status": "state_dir_unavailable", "gift_submission_enabled": False,
        }
        return planned
    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger.get("pending")
    if isinstance(pending, dict):
        plan["faction_gift_private_candidate_v1"] = {
            "status": "pending_recovery_required",
            "request_id": pending["request_id"],
            "source_faction_id": pending["source_faction_id"],
            "recipient_character_id": pending["recipient_character_id"],
            "gift_submission_enabled": False,
            "public_capability_advertised": False,
        }
        return planned
    if not callable(query):
        return planned
    root = root_view.get("root")
    if not isinstance(root, dict):
        return planned
    candidate = query(
        snapshot=snapshot, same_frame_root=root,
        minimum_gold_reserve_raw=10_000_000,
    )
    if not isinstance(candidate, dict):
        raise BridgeUnavailableError("private faction candidate query returned a non-object")
    plan["faction_gift_private_candidate_v1"] = candidate
    return planned
