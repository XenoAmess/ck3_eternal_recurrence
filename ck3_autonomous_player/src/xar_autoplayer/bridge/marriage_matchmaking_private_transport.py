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
PRIVATE_OBSERVED_HEIR_MARRIAGE_STEP_V1 = (
    "query-observed-heir-marriage-choices-v1-private"
)
OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_STEP_V1 = (
    "query-observed-first-heir-marriage-legality-v1"
)
OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_SCHEMA_V1 = (
    "xar.ck3.observed-first-heir-marriage-legality.v1"
)


def query_observed_heir_marriage_private_v1(
    driver: object, *, expected_native_revision: int,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Read native family legality after a public same-frame heir observation.

    No CharacterID parameter is accepted: the private bridge binds the primary
    first heir from the preceding public campaign-root query in its connection.
    This route does not invoke the human player's unavailable AI Strategy, does
    not produce an AI rank, and cannot submit a marriage action.
    """
    return _query_observed_heir_marriage_transport_v1(
        driver, expected_native_revision=expected_native_revision,
        timeout_seconds=timeout_seconds,
        step=PRIVATE_OBSERVED_HEIR_MARRIAGE_STEP_V1,
    )


def query_observed_first_heir_marriage_legality_v1(
    driver: object, *, expected_native_revision: int,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Candidate read-only schema; not registered or advertised before live."""
    result = _query_observed_heir_marriage_transport_v1(
        driver, expected_native_revision=expected_native_revision,
        timeout_seconds=timeout_seconds,
        step=OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_STEP_V1,
    )
    return {
        "schema": OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_SCHEMA_V1,
        "schema_version": 1,
        "exact_ck3_build": "1.19.0.6",
        "read_only": True,
        "advertised": False,
        "status": result["status"],
        "native_revision": result["native_revision"],
        "root_query_sequence": result["root_query_sequence"],
        "observed_first_heir_character_id": result[
            "observed_first_heir_character_id"],
        **({"unavailable_reason": result["unavailable_reason"]}
           if result["status"] == "unavailable" else {
               "query_sequence": result["query_sequence"],
               "candidates": result["candidates"],
               "native_legal_candidates": result["native_legal_candidates"],
               "diagnostics": result["diagnostics"],
               "family_subject_role_mismatches": result[
                   "family_subject_role_mismatches"],
           }),
    }


def _query_observed_heir_marriage_transport_v1(
    driver: object, *, expected_native_revision: int,
    timeout_seconds: float, step: str,
) -> dict[str, object]:
    before = driver.take_snapshot()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        type(expected_native_revision) is not int
        or expected_native_revision <= 0
        or before.get("native_revision") != expected_native_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or type(played_id) is not int
        or played_id <= 0
        or type(before.get("revision")) is not int
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError(
            "observed-heir marriage requires a current paused living-player map frame"
        )
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    root = driver._execute_campaign_root_context_v1_query(
        expected_revision=before["revision"]
    )
    if root.get("status") != "available":
        raise BridgeUnavailableError("public campaign-root first-heir read unavailable")
    if type(root.get("query_sequence")) is not int or root["query_sequence"] <= 0:
        raise BridgeUnavailableError("public campaign-root query sequence absent")
    partition = root.get("held_title_partition")
    if not isinstance(partition, list):
        raise BridgeUnavailableError("public campaign-root partition malformed")
    primary = [row for row in partition if isinstance(row, dict) and
               row.get("primary") is True]
    if len(primary) != 1:
        raise BridgeUnavailableError("public campaign-root primary title absent")
    heir_id = primary[0].get("first_heir_character_id")
    if heir_id is not None and (type(heir_id) is not int or heir_id <= 0):
        raise BridgeUnavailableError("public campaign-root first-heir ID malformed")
    _require_same_paused_frame(driver.take_snapshot(), before,
                               expected_native_revision, played_id)
    request_id = "m5-heir-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": step,
        "expected_revision": expected_native_revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(timeout_seconds)
    )
    if frame is None:
        raise BridgeUnavailableError(
            "observed-heir marriage private command_result timed out"
        )
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "observed-heir marriage private query RED: " +
            str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if (
        not isinstance(result, dict)
        or result.get("step") != step
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("subject_source") !=
           "public_campaign_root_primary_first_heir"
        or result.get("subject_character_id") !=
           (heir_id if heir_id is not None else -1)
        or type(result.get("query_sequence")) is not int
        or result["query_sequence"] <= 0
    ):
        raise BridgeUnavailableError(
            "observed-heir marriage private result disagrees with public heir"
        )
    _require_same_paused_frame(driver.take_snapshot(), before,
                               expected_native_revision, played_id)
    if result.get("status") == "unavailable":
        reason = result.get("unavailable_reason")
        if not isinstance(reason, str) or not reason:
            raise BridgeUnavailableError(
                "observed-heir marriage unavailable reason absent"
            )
        return {"status": "unavailable", "unavailable_reason": reason,
                "observed_first_heir_character_id": heir_id,
                "root_query_sequence": root.get("query_sequence"),
                "public_campaign_root": root,
                "native_revision": expected_native_revision}
    if result.get("status") != "available" or heir_id is None:
        raise BridgeUnavailableError(
            "observed-heir marriage private status is inconsistent"
        )
    rows = result.get("family_candidates")
    if not isinstance(rows, list):
        raise BridgeUnavailableError("observed-heir marriage rows absent")
    seen: set[int] = set()
    legal_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise BridgeUnavailableError("observed-heir marriage row malformed")
        candidate_id = row.get("candidate_character_id")
        if (
            type(candidate_id) is not int or candidate_id <= 0
            or candidate_id in seen
            or row.get("played_character_id") != played_id
            or row.get("subject_character_id") != heir_id
            or type(row.get("recipient_matchmaker_character_id")) is not int
            or row["recipient_matchmaker_character_id"] <= 0
            or type(row.get("intermediary_character_id")) is not int
            or row["intermediary_character_id"] < -1
            or row.get("native_rank") is not None
            or row.get("complete_can_send") is not True
            or type(row.get("recipient_ai_accept_raw")) is not int
            or type(row.get("recipient_answer_status_raw")) is not int
            or not 0 <= row["recipient_answer_status_raw"] <= 255
            or type(row.get("recipient_answer_allows_send")) is not bool
        ):
            raise BridgeUnavailableError(
                "observed-heir marriage row lost native identity or legality"
            )
        answer_status = row["recipient_answer_status_raw"]
        if (
            answer_status not in {0, 1, 2}
            or row["recipient_answer_allows_send"] is not
               (answer_status != 2)
        ):
            raise BridgeUnavailableError(
                "observed-heir marriage native final answer mapping disagrees"
            )
        seen.add(candidate_id)
        if row["recipient_answer_allows_send"]:
            legal_rows.append(row)
    diagnostics = result.get("arrange_marriage_diagnostics")
    if not isinstance(diagnostics, dict):
        raise BridgeUnavailableError("observed-heir marriage diagnostics absent")
    if (
        type(diagnostics.get("slots_scanned")) is not int
        or type(diagnostics.get("storage_capacity")) is not int
        or diagnostics["slots_scanned"] < 0
        or type(result.get("family_subject_role_mismatches")) is not int
        or result["family_subject_role_mismatches"] < 0
    ):
        raise BridgeUnavailableError(
            "observed-heir marriage native enumeration diagnostics malformed"
        )
    if diagnostics.get("slots_scanned") != diagnostics.get("storage_capacity"):
        raise BridgeUnavailableError(
            "observed-heir marriage native storage enumeration incomplete"
        )
    return {"status": "available", "query_sequence": result["query_sequence"],
            "observed_first_heir_character_id": heir_id,
            "root_query_sequence": root.get("query_sequence"),
            "public_campaign_root": root,
            "native_revision": expected_native_revision,
            "candidates": rows, "native_legal_candidates": legal_rows,
            "diagnostics": diagnostics,
            "family_subject_role_mismatches":
                result.get("family_subject_role_mismatches")}


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
        or not isinstance(played, dict)
        or played.get("alive") is not True
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
        or after_played.get("alive") is not True
    ):
        raise BridgeUnavailableError("ranked marriage frame changed before result consumption")
