"""Controlled read-only transport for the unadvertised ranked-marriage gate.

The private CMake option must be enabled in the sealed candidate DLL. This
function sends one explicit native protocol request; it is absent from the
production action-step registry and MCP tool list until paused live evidence
closes the query gate.
"""

from __future__ import annotations

import uuid

from .marriage_matchmaking_contract import normalize_ranked_marriage_observation
from .driver import BridgeUnavailableError


PRIVATE_RANKED_MARRIAGE_STEP_V1 = "query-ranked-marriage-candidates-v1-private"


def query_ranked_marriage_private_v1(
    driver: object,
    *,
    expected_native_revision: int,
    timeout_seconds: float = 20.0,
) -> dict[str, object]:
    """Run one bounded paused query without registering a public capability."""
    snapshot = driver.take_snapshot()
    native_revision = snapshot.get("native_revision")
    if type(expected_native_revision) is not int or expected_native_revision <= 0:
        raise ValueError("expected_native_revision must identify one native frame")
    if native_revision != expected_native_revision:
        raise ValueError("ranked marriage native revision changed before submission")
    played = snapshot.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or type(played_id) is not int
        or played_id <= 0
        or type(snapshot.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError("ranked marriage requires a paused living-player map frame")
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "m5-rank-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": PRIVATE_RANKED_MARRIAGE_STEP_V1,
        "expected_revision": expected_native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("ranked marriage private command_result timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "ranked marriage private query RED: " + str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if (
        not isinstance(result, dict)
        or result.get("step") != PRIVATE_RANKED_MARRIAGE_STEP_V1
        or result.get("accepted") is not True
    ):
        raise BridgeUnavailableError("ranked marriage private result shape changed")
    status = result.get("status")
    if status == "unavailable":
        reason = result.get("unavailable_reason")
        if not isinstance(reason, str) or not reason:
            raise BridgeUnavailableError("ranked marriage unavailable reason is absent")
        _require_same_paused_frame(driver.take_snapshot(), snapshot, expected_native_revision, played_id)
        return {"status": "unavailable", "unavailable_reason": reason,
                "native_revision": expected_native_revision}
    if status != "available":
        raise BridgeUnavailableError("ranked marriage private status is unknown")
    sequence = result.get("query_sequence")
    if type(sequence) is not int or sequence <= 0:
        raise BridgeUnavailableError("ranked marriage private query_sequence is malformed")
    normalized = normalize_ranked_marriage_observation(
        result.get("ranked_marriage_observation"),
        snapshot_id=f"native:{expected_native_revision}",
        public_revision=expected_native_revision,
        native_revision=expected_native_revision,
        date_raw=snapshot["date_raw"],
        played_character_id=played_id,
    )
    _require_same_paused_frame(driver.take_snapshot(), snapshot, expected_native_revision, played_id)
    return {"status": "available", "query_sequence": sequence,
            "observation": normalized}


def _require_same_paused_frame(
    after: dict[str, object], before: dict[str, object],
    expected_native_revision: int, played_id: int,
) -> None:
    after_played = after.get("played_character")
    if (
        after.get("native_revision") != expected_native_revision
        or after.get("date_raw") != before["date_raw"]
        or after.get("paused") is not True
        or after.get("map_ready") is not True
        or not isinstance(after_played, dict)
        or after_played.get("character_id") != played_id
    ):
        raise BridgeUnavailableError("ranked marriage frame changed before result consumption")
