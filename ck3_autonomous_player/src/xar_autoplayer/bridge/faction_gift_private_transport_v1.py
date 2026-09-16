"""Scoped private native read for the unadvertised faction gift candidate.

Normal GameplayBridgeService planning may consume this same-frame query. It
does not expose an action step or submit a gift while the cold recovery query
is absent from the exact-build native bridge.
"""

from __future__ import annotations

from typing import Mapping
import uuid

from .driver import BridgeUnavailableError
from ..faction_gift_formal_candidate_v1 import (
    PRIVATE_QUERY_STEP, choose_private_faction_gift_candidate_v1,
)


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    played = snapshot.get("played_character")
    return (
        snapshot.get("snapshot_id"), snapshot.get("revision"),
        snapshot.get("native_revision"), snapshot.get("date_raw"),
        snapshot.get("paused"), snapshot.get("map_ready"),
        played.get("character_id") if isinstance(played, Mapping) else None,
        played.get("alive") if isinstance(played, Mapping) else None,
        snapshot.get("active_event"), snapshot.get("pending_character_interaction"),
    )


def query_faction_gift_private_candidate_v1(
    driver: object, *, snapshot: Mapping[str, object],
    same_frame_root: Mapping[str, object], minimum_gold_reserve_raw: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Read one exact native selected member through the owned driver pipe."""
    if not isinstance(timeout_seconds, (float, int)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ValueError("faction gift query timeout must be positive")
    before = driver.take_internal_semantic_snapshot()
    if _binding(before) != _binding(snapshot):
        raise BridgeUnavailableError("private faction query source frame changed")
    actor = before.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    if not (
        before.get("paused") is True and before.get("map_ready") is True
        and isinstance(actor, Mapping) and actor.get("alive") is True
        and type(actor_id) is int and actor_id > 0
        and type(revision) is int and revision > 0
        and type(date_raw) is int and date_raw >= 0
        and before.get("active_event") is None
        and before.get("pending_character_interaction") is None
        and before.get("one_life_terminal_reason") is None
    ):
        raise BridgeUnavailableError("private faction query requires an ordinary paused living-player frame")
    diagnostics = driver.diagnostics()
    heartbeat = diagnostics.get("last_heartbeat")
    route = heartbeat.get("g2_faction_gift_mitigation_async_glue_v1") if isinstance(heartbeat, Mapping) else None
    if not isinstance(route, Mapping) or route.get("private_build") is not True:
        return {"status": "private_route_off", "public_capability_advertised": False,
                "gift_submission_enabled": False}
    government = same_frame_root.get("government")
    if (
        same_frame_root.get("snapshot_revision") != revision
        or same_frame_root.get("date_raw") != date_raw
        or same_frame_root.get("player_character_id") != actor_id
        or not isinstance(government, Mapping)
        or government.get("key") != "feudal_government"
    ):
        raise BridgeUnavailableError("private faction query lacks same-frame public root")
    count = same_frame_root.get("player_targeting_faction_count")
    if type(count) is not int or count <= 0:
        raise BridgeUnavailableError("private faction query lacks a nonempty exact targeting count")
    request_id = "faction-gift-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": PRIVATE_QUERY_STEP,
        "expected_revision": revision, "expected_date_raw": date_raw,
        "expected_player_character_id": actor_id,
    })
    frame = driver.state.wait_for_command_result(request_id, timeout_seconds)
    if frame is None:
        raise BridgeUnavailableError("private faction query command_result timed out")
    if (
        frame.get("type") != "command_result" or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id or frame.get("ok") is not True
    ):
        raise BridgeUnavailableError(
            "private faction query returned RED or malformed command_result: " +
            str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if not isinstance(result, Mapping):
        raise BridgeUnavailableError("private faction query result is missing")
    after = driver.take_internal_semantic_snapshot()
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError("private faction query crossed its paused frame")
    return choose_private_faction_gift_candidate_v1(
        before, same_frame_root, result,
        minimum_gold_reserve_raw=minimum_gold_reserve_raw,
    )
