"""Private same-day material observation for natural epidemic_events.0110.c."""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.driver import BridgeUnavailableError


EVENT_KEY = "epidemic_events.0110"
OPTION_STEP = "select-event-option-3"


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _frame(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        raise BridgeUnavailableError("epidemic recovery has no paused snapshot")
    actor = snapshot.get("played_character")
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(snapshot.get("snapshot_id"), str)
        and _positive(snapshot.get("revision"))
        and _positive(snapshot.get("native_revision"))
        and isinstance(snapshot.get("date_raw"), int)
        and not isinstance(snapshot.get("date_raw"), bool)
        and isinstance(actor, Mapping)
        and actor.get("alive") is True
        and _positive(actor.get("character_id"))
    ):
        raise BridgeUnavailableError("epidemic recovery needs one paused living player")
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "revision": snapshot["revision"],
        "native_revision": snapshot["native_revision"],
        "date_raw": snapshot["date_raw"],
        "episode_run_id": snapshot.get("episode_run_id"),
        "actor_character_id": actor["character_id"],
    }


def _legitimacy(service: object, frame: Mapping[str, object]) -> dict[str, object]:
    root = service.query_campaign_root_context_v1(
        expected_revision=frame["revision"]
    )
    context = root.get("campaign_root_context") if isinstance(root, Mapping) else None
    if not (
        isinstance(context, Mapping)
        and context.get("player_character_id") == frame["actor_character_id"]
        and root.get("queried_snapshot_id") == frame["snapshot_id"]
        and root.get("queried_revision") == frame["revision"]
        and root.get("queried_native_revision") == frame["native_revision"]
    ):
        raise BridgeUnavailableError("epidemic recovery legitimacy query drifted")
    value = context.get("player_legitimacy_v1")
    if isinstance(value, Mapping) and value.get("status") == "available":
        fixed = value.get("value")
        if isinstance(fixed, Mapping) and isinstance(fixed.get("raw"), int) and not isinstance(fixed.get("raw"), bool) and fixed.get("scale") == 100_000:
            return {"status": "available", "raw": fixed["raw"], "scale": 100_000}
    return {
        "status": "unavailable",
        "raw": None,
        "unavailable_reason": (
            value.get("unavailable_reason")
            if isinstance(value, Mapping) else "field_not_published"
        ),
    }


def _counties(query: object) -> list[dict[str, object]]:
    value = query.get("player_epidemic_recovery") if isinstance(query, Mapping) else None
    if not isinstance(value, Mapping) or value.get("status") != "available":
        raise BridgeUnavailableError("epidemic recovery county observer unavailable")
    rows = value.get("counties")
    if not isinstance(rows, list):
        raise BridgeUnavailableError("epidemic recovery county rows unavailable")
    return [dict(row) for row in rows]


def capture_epidemic_recovery_before_option(
    service: object, candidate: object,
) -> dict[str, object] | None:
    """Freeze exact native option c's target titles before its after block clears them."""
    if not isinstance(candidate, Mapping):
        return None
    plan = candidate.get("plan")
    if not isinstance(plan, Mapping):
        return None
    decision = plan.get("event_decision")
    event = plan.get("active_event")
    if not (
        plan.get("phase") == "active_event_registry_choice"
        and candidate.get("selected_step") == OPTION_STEP
        and isinstance(decision, Mapping)
        and decision.get("status") == "recommended"
        and decision.get("event_definition_key") == EVENT_KEY
        and decision.get("selected_native_option_index") == 2
        and decision.get("selected_option_number") == 3
        and isinstance(event, Mapping)
        and _positive(event.get("instance_id"))
    ):
        return None
    snapshot = service.snapshot()
    frame = _frame(snapshot)
    active = snapshot.get("active_event")
    if not (
        candidate.get("snapshot_id") == frame["snapshot_id"]
        and candidate.get("revision") == frame["revision"]
        and isinstance(active, Mapping)
        and active.get("instance_id") == event["instance_id"]
    ):
        raise BridgeUnavailableError("epidemic recovery candidate crossed its event frame")
    query = service.query_player_epidemic_recovery_private_v1(
        expected_revision=frame["revision"],
        expected_event_instance_id=event["instance_id"],
    )
    rows = _counties(query)
    if not rows:
        raise BridgeUnavailableError("epidemic recovery target list is empty")
    legitimacy = _legitimacy(service, frame)
    if _frame(service.snapshot()) != frame:
        raise BridgeUnavailableError("epidemic recovery pre-action frame drifted")
    return {
        "schema": "private-epidemic-recovery-near-pair-v1",
        "status": "pre_captured",
        "event_definition_key": EVENT_KEY,
        "event_instance_id": event["instance_id"],
        "option_step": OPTION_STEP,
        "before_frame": frame,
        "before_counties": rows,
        "before_legitimacy": legitimacy,
    }


def observe_epidemic_recovery_after_option(
    service: object, before: Mapping[str, object], after_snapshot: object,
) -> dict[str, object]:
    """Read the frozen titles in an independent paused frame on the same date."""
    after = _frame(after_snapshot)
    start = before.get("before_frame")
    if not (
        isinstance(start, Mapping)
        and after["date_raw"] == start.get("date_raw")
        and after["actor_character_id"] == start.get("actor_character_id")
        and after["episode_run_id"] == start.get("episode_run_id")
        and after["native_revision"] > start.get("native_revision", 0)
        and after["revision"] > start.get("revision", 0)
    ):
        raise BridgeUnavailableError("epidemic recovery post-action frame is not same-day and later")
    active = after_snapshot.get("active_event")
    if isinstance(active, Mapping) and active.get("instance_id") == before.get("event_instance_id"):
        raise BridgeUnavailableError("epidemic recovery old event instance remains active")
    before_rows = before.get("before_counties")
    if not isinstance(before_rows, list) or not before_rows:
        raise BridgeUnavailableError("epidemic recovery lost its pre-action title list")
    rows: list[dict[str, object]] = []
    for old in before_rows:
        if not isinstance(old, Mapping) or not _positive(old.get("landed_title_id")):
            raise BridgeUnavailableError("epidemic recovery pre-action title is malformed")
        title_id = old["landed_title_id"]
        query = service.query_player_epidemic_recovery_private_v1(
            expected_revision=after["revision"], requested_title_id=title_id,
        )
        current_rows = _counties(query)
        if len(current_rows) != 1 or current_rows[0].get("landed_title_id") != title_id:
            raise BridgeUnavailableError("epidemic recovery post-action title identity drifted")
        current = current_rows[0]
        newly_present = [
            kind for kind in ("minor", "tiny")
            if old.get(f"{kind}_present") is False
            and current.get(f"{kind}_present") is True
        ]
        rows.append({
            "landed_title_id": title_id,
            "before": dict(old),
            "after": current,
            "newly_present": newly_present,
            "status": (
                "new_modifier_presence" if len(newly_present) == 1
                else "unexpected_both_modifiers_new"
                if len(newly_present) > 1
                else "preexisting_presence_ambiguous"
                if old.get("minor_present") is True or old.get("tiny_present") is True
                else "no_modifier_presence_observed"
            ),
        })
    legitimacy = _legitimacy(service, after)
    if _frame(service.snapshot()) != after:
        raise BridgeUnavailableError("epidemic recovery post-action frame drifted")
    old_legitimacy = before.get("before_legitimacy")
    delta = (
        legitimacy["raw"] - old_legitimacy["raw"]
        if isinstance(old_legitimacy, Mapping)
        and old_legitimacy.get("status") == "available"
        and legitimacy.get("status") == "available"
        else None
    )
    return {
        "schema": before.get("schema"),
        "status": (
            "verified_new_modifier_presence"
            if all(row["status"] == "new_modifier_presence" for row in rows)
            else "partial_or_unverified"
        ),
        "event_definition_key": EVENT_KEY,
        "event_instance_id": before.get("event_instance_id"),
        "option_step": OPTION_STEP,
        "before_frame": dict(start),
        "after_frame": after,
        "counties": rows,
        "legitimacy": {
            "before": old_legitimacy,
            "after": legitimacy,
            "delta_raw": delta,
            "same_date_observation": True,
        },
        "date_advanced": False,
        "remaining_days": {"status": "unavailable", "value": None},
    }
