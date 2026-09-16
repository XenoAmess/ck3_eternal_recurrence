"""Private exact-build typed Close route for one natural-death succession modal."""

from __future__ import annotations

import copy
import time
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import (
    query_current_timeline_blocker_context_private_v1,
)

CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP = (
    "continue-death-succession-modal-v1"
)
POST_CLOSE_QUERY_LIMIT = 8
POST_CLOSE_QUERY_INTERVAL_SECONDS = 0.05


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


def _post_query_binding(snapshot: Mapping[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "episode_character_id": snapshot.get("episode_character_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "played_character_id": (
            played.get("character_id") if isinstance(played, Mapping) else None
        ),
        "played_character_alive": (
            played.get("alive") if isinstance(played, Mapping) else None
        ),
    }


def _submitted_unconfirmed_result(
    *,
    ack: dict[str, object],
    initial: dict[str, object],
    post_attempts: list[dict[str, object]],
    date_raw: int,
    snapshot: Mapping[str, object],
    failure: str,
) -> dict[str, object]:
    last_query = next(
        (
            attempt.get("query")
            for attempt in reversed(post_attempts)
            if isinstance(attempt.get("query"), dict)
        ),
        None,
    )
    return {
        **copy.deepcopy(ack),
        "status": "submitted_unconfirmed",
        "material_result_verified": False,
        "submission_ack": copy.deepcopy(ack),
        "initial_query": copy.deepcopy(initial),
        "postcondition_queries": [
            copy.deepcopy(attempt["query"])
            for attempt in post_attempts
            if isinstance(attempt.get("query"), dict)
        ],
        "postcondition_query": copy.deepcopy(last_query),
        "post_observation_revision": (
            last_query.get("observation_revision")
            if isinstance(last_query, dict)
            else None
        ),
        "post_query_attempts": copy.deepcopy(post_attempts),
        "post_failure": failure,
        "life_advance_result": None,
        "starting_date_raw": date_raw,
        "ending_date_raw": snapshot.get("date_raw"),
        "ending_revision": snapshot.get("revision"),
        "ending_native_revision": snapshot.get("native_revision"),
    }


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

    try:
        after_ack = driver.take_snapshot()
    except Exception as error:
        return _submitted_unconfirmed_result(
            ack=ack,
            initial=initial,
            post_attempts=[],
            date_raw=date_raw,
            snapshot=before,
            failure=(
                "post-Close snapshot failed: "
                f"{type(error).__name__}: {error}"
            ),
        )
    if (
        after_ack.get("revision") != expected_revision
        or after_ack.get("native_revision") != native_revision
        or after_ack.get("date_raw") != date_raw
        or _episode_binding(after_ack) != source_episode
    ):
        return _submitted_unconfirmed_result(
            ack=ack,
            initial=initial,
            post_attempts=[],
            date_raw=date_raw,
            snapshot=after_ack,
            failure=(
                "death-succession Close crossed its source episode before "
                "postcondition verification"
            ),
        )
    deadline = time.monotonic() + float(timeout_seconds)
    post_attempts: list[dict[str, object]] = []
    post: dict[str, object] | None = None
    last_snapshot = after_ack
    prior_observation_revision = action_observation_revision
    false_field = {
        "status": "available",
        "value": False,
        "unavailable_reason": None,
    }
    for attempt_number in range(1, POST_CLOSE_QUERY_LIMIT + 1):
        if time.monotonic() >= deadline:
            return _submitted_unconfirmed_result(
                ack=ack,
                initial=initial,
                post_attempts=post_attempts,
                date_raw=date_raw,
                snapshot=last_snapshot,
                failure="bounded post-Close query timeout expired",
            )
        attempt: dict[str, object] = {
            "attempt": attempt_number,
            "query": None,
            "error": None,
            "binding": None,
        }
        try:
            query_before = driver.take_snapshot()
            last_snapshot = query_before
            attempt["binding"] = _post_query_binding(query_before)
            if (
                query_before.get("revision") != expected_revision
                or query_before.get("native_revision") != native_revision
                or query_before.get("date_raw") != date_raw
                or query_before.get("paused") is not True
                or query_before.get("map_ready") is not True
                or _episode_binding(query_before) != source_episode
            ):
                raise BridgeUnavailableError(
                    "post-Close query crossed the paused source episode binding"
                )
            remaining = max(0.001, deadline - time.monotonic())
            post = query_current_timeline_blocker_context_private_v1(
                driver,
                expected_revision=expected_revision,
                timeout_seconds=remaining,
            )
            attempt["query"] = copy.deepcopy(post)
            post_observation_revision = _positive_int(
                post.get("observation_revision"), "post observation_revision"
            )
            if post_observation_revision <= prior_observation_revision:
                raise BridgeUnavailableError(
                    "post-Close observation revision did not strictly increase"
                )
            prior_observation_revision = post_observation_revision
            post_attempts.append(attempt)
            post_context = post["current_timeline_blocker_context"]
            if (
                post_context.get("status") == "available"
                and post_context.get("identity") == "none"
                and post_context.get("blocks_simulation") == false_field
                and post_context.get("has_open_succession") == false_field
            ):
                break
            time.sleep(
                min(
                    POST_CLOSE_QUERY_INTERVAL_SECONDS,
                    max(0.0, deadline - time.monotonic()),
                )
            )
        except Exception as error:
            attempt["error"] = f"{type(error).__name__}: {error}"
            post_attempts.append(attempt)
            return _submitted_unconfirmed_result(
                ack=ack,
                initial=initial,
                post_attempts=post_attempts,
                date_raw=date_raw,
                snapshot=last_snapshot,
                failure=attempt["error"],
            )
    else:
        return _submitted_unconfirmed_result(
            ack=ack,
            initial=initial,
            post_attempts=post_attempts,
            date_raw=date_raw,
            snapshot=last_snapshot,
            failure=(
                "bounded post-Close queries exhausted while the modal or "
                "succession predicates remained uncleared"
            ),
        )

    if post is None:  # loop success cannot occur without a normalized query
        return _submitted_unconfirmed_result(
            ack=ack,
            initial=initial,
            post_attempts=post_attempts,
            date_raw=date_raw,
            snapshot=last_snapshot,
            failure="post-Close query loop produced no material observation",
        )
    post_observation_revision = _positive_int(
        post.get("observation_revision"), "post observation_revision"
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
        # Keep the submission receipt distinct from the independently
        # observed material result.  The ACK explicitly says that it did not
        # prove the Close took effect; only the later query and life-advance
        # can promote this bounded operation to materially_verified.
        "submission_ack": copy.deepcopy(ack),
        "initial_query": initial,
        "postcondition_queries": [
            copy.deepcopy(attempt["query"])
            for attempt in post_attempts
            if isinstance(attempt.get("query"), dict)
        ],
        "postcondition_query": post,
        "post_observation_revision": post_observation_revision,
        "post_query_attempts": copy.deepcopy(post_attempts),
        "post_failure": None,
        "life_advance_result": copy.deepcopy(life_result),
        "starting_date_raw": date_raw,
        "ending_date_raw": final_date,
        "ending_revision": after_advance.get("revision"),
        "ending_native_revision": after_advance.get("native_revision"),
    }
