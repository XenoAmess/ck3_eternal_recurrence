"""Private same-frame transport for the unadvertised timeline-blocker query."""

from __future__ import annotations

import copy
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_context_contract import (
    QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
    normalize_current_timeline_blocker_context_v1,
)


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    played = snapshot.get("played_character")
    return (
        snapshot.get("snapshot_id"),
        snapshot.get("revision"),
        snapshot.get("native_revision"),
        snapshot.get("date_raw"),
        snapshot.get("paused"),
        snapshot.get("map_ready"),
        played.get("character_id") if isinstance(played, Mapping) else None,
        played.get("alive") if isinstance(played, Mapping) else None,
        copy.deepcopy(snapshot.get("active_event")),
        copy.deepcopy(snapshot.get("pending_character_interaction")),
        snapshot.get("one_life_terminal_reason"),
    )


def query_current_timeline_blocker_context_private_v1(
    driver: object,
    *,
    expected_revision: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Issue one zero-argument typed query without capability advertisement."""
    if getattr(driver, "allow_private_current_timeline_blocker_query", False) is not True:
        raise UnsupportedStepError("private timeline-blocker query is disabled")
    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
    ):
        raise BridgeUnavailableError(
            "timeline-blocker query requires one current paused map frame"
        )
    request_id = "timeline-blocker-" + uuid.uuid4().hex
    driver.endpoint.send(
        {
            "type": "execute_step",
            "protocol_version": 1,
            "request_id": request_id,
            "step": QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP,
            "expected_revision": native_revision,
        }
    )
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("timeline-blocker command_result timed out")
    if (
        frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
        or frame.get("ok") is not True
    ):
        raise BridgeUnavailableError(
            "timeline-blocker private query returned RED or a malformed frame: "
            + str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    expected_keys = {
        "step",
        "accepted",
        "status",
        "query_sequence",
        "observation_revision",
        "snapshot_revision",
        "current_timeline_blocker_context",
        "private_build",
        "read_only",
        "advertised",
        "backend_id",
    }
    if (
        not isinstance(result, dict)
        or set(result) != expected_keys
        or result.get("step") != QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP
        or result.get("accepted") is not True
        or result.get("snapshot_revision") != native_revision
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("backend_id") != "native-headless"
        or isinstance(result.get("query_sequence"), bool)
        or not isinstance(result.get("query_sequence"), int)
        or result["query_sequence"] <= 0
        or isinstance(result.get("observation_revision"), bool)
        or not isinstance(result.get("observation_revision"), int)
        or result["observation_revision"] <= 0
    ):
        raise BridgeUnavailableError("timeline-blocker private result shape changed")
    try:
        normalized = normalize_current_timeline_blocker_context_v1(
            result.get("current_timeline_blocker_context"),
            expected_date_raw=date_raw,
            expected_snapshot_revision=native_revision,
        )
    except ValueError as error:
        raise BridgeUnavailableError(
            f"timeline-blocker private result is malformed: {error}"
        ) from error
    if result.get("status") != normalized["status"]:
        raise BridgeUnavailableError("timeline-blocker envelope status disagrees")
    after = driver.take_snapshot()
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError("timeline-blocker query crossed its paused frame")
    return {
        **result,
        "current_timeline_blocker_context": normalized,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": before.get("revision"),
        "queried_native_revision": native_revision,
        "date_raw": date_raw,
    }
