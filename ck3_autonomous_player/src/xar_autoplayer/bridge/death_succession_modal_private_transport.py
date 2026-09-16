"""Private exact-build typed Close route for one natural-death succession modal."""

from __future__ import annotations

import copy
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import (
    query_current_timeline_blocker_context_private_v1,
)

CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP = (
    "continue-death-succession-modal-v1"
)


def _episode_binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    played = snapshot.get("played_character")
    return (
        snapshot.get("episode_character_id"),
        snapshot.get("episode_run_id"),
        played.get("character_id") if isinstance(played, Mapping) else None,
        played.get("alive") if isinstance(played, Mapping) else None,
    )


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BridgeUnavailableError(f"{label} must be a positive integer")
    return value


def continue_death_succession_modal_private_v1(
    driver: object,
    *,
    expected_revision: int,
    expected_played_character_id: int,
    expected_episode_run_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Close once, independently observe its result, then prove date advance."""
    if (
        getattr(driver, "allow_private_death_succession_modal_continue", False)
        is not True
    ):
        raise UnsupportedStepError("private death-succession Close is disabled")
    if (
        isinstance(expected_revision, bool)
        or not isinstance(expected_revision, int)
        or expected_revision < 0
        or isinstance(expected_played_character_id, bool)
        or not isinstance(expected_played_character_id, int)
        or expected_played_character_id <= 0
        or not isinstance(expected_episode_run_id, str)
        or not expected_episode_run_id
    ):
        raise ValueError("death-succession Close binding is malformed")

    before = driver.take_snapshot()
    played = before.get("played_character")
    native_revision = _positive_int(before.get("native_revision"), "native_revision")
    date_raw = before.get("date_raw")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or played.get("character_id") != expected_played_character_id
        or before.get("episode_character_id") != expected_played_character_id
        or before.get("episode_run_id") != expected_episode_run_id
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
    ):
        raise BridgeUnavailableError(
            "death-succession Close requires the bound paused successor episode"
        )
    source_episode = _episode_binding(before)

    initial = query_current_timeline_blocker_context_private_v1(
        driver,
        expected_revision=expected_revision,
        timeout_seconds=timeout_seconds,
    )
    context = initial["current_timeline_blocker_context"]
    if (
        context.get("status") != "available"
        or context.get("identity") != "death_succession_modal"
        or context.get("can_continue")
        != {"status": "available", "value": True, "unavailable_reason": None}
        or context.get("blocks_simulation")
        != {"status": "available", "value": True, "unavailable_reason": None}
        or context.get("has_open_succession")
        != {"status": "available", "value": True, "unavailable_reason": None}
    ):
        raise BridgeUnavailableError(
            "fresh death-succession modal preconditions are not satisfied"
        )

    request_id = "death-succession-close-" + uuid.uuid4().hex
    driver.endpoint.send(
        {
            "type": "execute_step",
            "protocol_version": 1,
            "request_id": request_id,
            "step": CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP,
            "expected_revision": native_revision,
            "expected_date_raw": date_raw,
            "expected_played_character_id": expected_played_character_id,
        }
    )
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError(
            "death-succession Close ACK timed out; action state is unknown"
        )
    if (
        frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
        or frame.get("ok") is not True
        or not isinstance(frame.get("result"), dict)
    ):
        raise BridgeUnavailableError(
            "death-succession Close returned RED; action state is unknown: "
            + str(frame.get("error") or "unknown")
        )
    ack = frame["result"]
    expected_ack_keys = {
        "step",
        "accepted",
        "status",
        "snapshot_revision",
        "date_raw",
        "played_character_id",
        "action_observation_revision",
        "identity_verified",
        "can_continue_verified",
        "paused_by_succession_verified",
        "has_open_succession_verified",
        "controller_vtable_verified",
        "controller_open_verified",
        "close_invocations",
        "material_result_verified",
        "private_build",
        "advertised",
        "backend_id",
    }
    if (
        set(ack) != expected_ack_keys
        or ack.get("step") != CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP
        or ack.get("accepted") is not True
        or ack.get("status") != "submitted"
        or ack.get("snapshot_revision") != native_revision
        or ack.get("date_raw") != date_raw
        or ack.get("played_character_id") != expected_played_character_id
        or ack.get("close_invocations") != 1
        or ack.get("material_result_verified") is not False
        or ack.get("private_build") is not True
        or ack.get("advertised") is not False
        or ack.get("backend_id") != "native-headless"
        or any(
            ack.get(key) is not True
            for key in (
                "identity_verified",
                "can_continue_verified",
                "paused_by_succession_verified",
                "has_open_succession_verified",
                "controller_vtable_verified",
                "controller_open_verified",
            )
        )
    ):
        raise BridgeUnavailableError(
            "death-succession Close ACK shape changed; action state is unknown"
        )
    action_observation_revision = _positive_int(
        ack.get("action_observation_revision"), "action_observation_revision"
    )

    after_ack = driver.take_snapshot()
    if (
        after_ack.get("revision") != expected_revision
        or after_ack.get("native_revision") != native_revision
        or after_ack.get("date_raw") != date_raw
        or _episode_binding(after_ack) != source_episode
    ):
        raise BridgeUnavailableError(
            "death-succession Close crossed its source episode before verification"
        )
    post = query_current_timeline_blocker_context_private_v1(
        driver,
        expected_revision=expected_revision,
        timeout_seconds=timeout_seconds,
    )
    post_observation_revision = _positive_int(
        post.get("observation_revision"), "post observation_revision"
    )
    post_context = post["current_timeline_blocker_context"]
    false_field = {
        "status": "available",
        "value": False,
        "unavailable_reason": None,
    }
    if (
        post_observation_revision <= action_observation_revision
        or post_context.get("status") != "available"
        or post_context.get("identity") != "none"
        or post_context.get("blocks_simulation") != false_field
        or post_context.get("has_open_succession") != false_field
    ):
        raise BridgeUnavailableError(
            "independent post-Close observation did not prove the modal cleared"
        )

    before_advance = driver.take_snapshot()
    if (
        before_advance.get("revision") != expected_revision
        or before_advance.get("date_raw") != date_raw
        or _episode_binding(before_advance) != source_episode
    ):
        raise BridgeUnavailableError(
            "successor episode changed before formal life-advance"
        )
    life_result = driver.execute_step(
        "life-advance", expected_revision=expected_revision
    )
    after_advance = driver.take_snapshot()
    final_date = after_advance.get("date_raw")
    if (
        isinstance(final_date, bool)
        or not isinstance(final_date, int)
        or final_date <= date_raw
        or _episode_binding(after_advance) != source_episode
    ):
        raise BridgeUnavailableError(
            "formal life-advance did not increase date after succession Close"
        )
    return {
        **copy.deepcopy(ack),
        "status": "materially_verified",
        "material_result_verified": True,
        "initial_query": initial,
        "postcondition_query": post,
        "post_observation_revision": post_observation_revision,
        "life_advance_result": copy.deepcopy(life_result),
        "starting_date_raw": date_raw,
        "ending_date_raw": final_date,
        "ending_revision": after_advance.get("revision"),
        "ending_native_revision": after_advance.get("native_revision"),
    }
