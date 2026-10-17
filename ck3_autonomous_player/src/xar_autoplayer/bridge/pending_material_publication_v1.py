"""Bound a pending material action before another ordinary opportunity read.

This is a planning barrier, not a receipt or permission to replay an action.
Only durable formal-action records with a source revision are admitted.
"""

from __future__ import annotations

from collections.abc import Mapping


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def classify_pending_material_v1(
    snapshot: Mapping[str, object], *, crown: object = None,
    construction: object = None, bridge_pid: object = None,
    bridge_creation_date: object = None,
) -> dict[str, object] | None:
    """Classify one durable pending intent without granting material credit."""
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    episode = snapshot.get("episode_run_id")
    native_revision = snapshot.get("native_revision")
    if (not _positive(actor_id) or not isinstance(episode, str) or not episode
            or not _positive(native_revision)):
        return None
    records = []
    if isinstance(crown, Mapping):
        if (crown.get("stage") in {"submission_unresolved", "receipt_pending"}
                and isinstance(crown.get("action_id"), str) and crown["action_id"]
                and _positive(crown.get("pre_native_revision"))
                and crown.get("episode_run_id") == episode
                and crown.get("actor_character_id") == actor_id):
            source = crown.get("source_context")
            same_process = (isinstance(source, Mapping)
                            and _positive(bridge_pid)
                            and source.get("bridge_pid") == bridge_pid
                            and source.get("episode_run_id") == episode)
            records.append(("crown", crown, same_process))
    if isinstance(construction, Mapping):
        if (isinstance(construction.get("action_request_id"), str)
                and construction["action_request_id"]
                and _positive(construction.get("pre_native_revision"))
                and construction.get("episode_run_id") == episode
                and construction.get("actor_character_id") == actor_id):
            same_process = (
                _positive(bridge_pid)
                and construction.get("source_bridge_pid") == bridge_pid
                and isinstance(bridge_creation_date, str) and bool(bridge_creation_date)
                and construction.get("source_bridge_creation_date") == bridge_creation_date
            )
            records.append(("construction", construction, same_process))
    if not records:
        return None
    if len(records) != 1:
        return {"status": "ambiguous", "domains": [row[0] for row in records],
                "business_credit": False}
    domain, pending, same_process = records[0]
    pre_revision = pending["pre_native_revision"]
    return {
        "status": ("await_publication" if same_process and native_revision <= pre_revision
                   else "ready" if same_process else "cold_receipt"),
        "domain": domain, "pending": dict(pending),
        "pre_native_revision": pre_revision, "observed_native_revision": native_revision,
        "same_process": same_process, "business_credit": False,
    }


def same_publication_scope_v1(before: Mapping[str, object],
                              after: Mapping[str, object]) -> bool:
    """An intermediate public update may change resources before Native rev."""
    old_actor = before.get("played_character")
    new_actor = after.get("played_character")
    old_diag = before.get("diagnostics")
    new_diag = after.get("diagnostics")
    return bool(
        isinstance(old_actor, Mapping) and isinstance(new_actor, Mapping)
        and old_actor.get("character_id") == new_actor.get("character_id")
        and old_actor.get("alive") is True and new_actor.get("alive") is True
        and before.get("episode_run_id") == after.get("episode_run_id")
        and isinstance(old_diag, Mapping) and isinstance(new_diag, Mapping)
        and _positive(old_diag.get("bridge_pid"))
        and old_diag.get("bridge_pid") == new_diag.get("bridge_pid")
        and old_diag.get("connection_generation") == new_diag.get("connection_generation")
        and type(before.get("date_raw")) is int
        and type(after.get("date_raw")) is int
        and after["date_raw"] >= before["date_raw"]
        and before.get("paused") is True and after.get("paused") is True
        and before.get("map_ready") is True and after.get("map_ready") is True
        and type(before.get("revision")) is int
        and type(after.get("revision")) is int
        and after["revision"] > before["revision"]
    )


def same_publication_owner_v1(before: Mapping[str, object],
                              after: Mapping[str, object]) -> bool:
    """Require both the same owner and a genuinely newer Native frame."""
    return bool(same_publication_scope_v1(before, after)
                and type(before.get("native_revision")) is int
                and type(after.get("native_revision")) is int
                and after["native_revision"] > before["native_revision"])


def can_advance_for_publication_v1(snapshot: Mapping[str, object]) -> bool:
    """One strict observation day is permitted only in a quiet map frame."""
    actor = snapshot.get("played_character")
    return bool(snapshot.get("paused") is True
                and snapshot.get("map_ready") is True
                and isinstance(actor, Mapping) and actor.get("alive") is True
                and snapshot.get("active_wars") == []
                and snapshot.get("player_armies") == []
                and snapshot.get("active_event") is None
                and snapshot.get("pending_character_interaction") is None
                and snapshot.get("one_life_terminal") is False)
