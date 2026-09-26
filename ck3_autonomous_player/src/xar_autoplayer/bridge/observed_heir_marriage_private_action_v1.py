"""Private exact-build first-heir marriage transport; never a public action."""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError


SUBMIT_STEP = "submit-observed-first-heir-marriage-v1-private"
RESULT_STEP = "query-observed-first-heir-marriage-result-v1-private"
SCHEMA = "xar.ck3.observed-first-heir-marriage-private-action.v1"


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _paused(driver: object) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    played = snapshot.get("played_character")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or not _positive(played.get("character_id"))
        or not _positive(snapshot.get("native_revision"))
    ):
        raise BridgeUnavailableError("heir marriage requires a paused living-player frame")
    return snapshot


def _command(driver: object, step: str, payload: dict[str, object],
             timeout_seconds: float) -> dict[str, object]:
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "m5-heir-action-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step, **payload,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("heir marriage private command timed out; state unknown")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("heir marriage private command RED: " +
                                     str(frame.get("error") or "unknown"))
    result = frame.get("result")
    if (
        not isinstance(result, dict)
        or result.get("step") != step
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("advertised") is not False
    ):
        raise BridgeUnavailableError("heir marriage private result shape changed")
    return result


def submit_observed_first_heir_marriage_private_v1(
    driver: object, *, legality: dict[str, object], candidate_character_id: int,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Submit a caller-chosen final-legal row; ACK is not a material result."""
    snapshot = _paused(driver)
    played_id = snapshot["played_character"]["character_id"]
    revision = snapshot["native_revision"]
    heir_id = legality.get("observed_first_heir_character_id")
    rows = legality.get("native_legal_candidates")
    if (
        legality.get("schema") !=
            "xar.ck3.observed-first-heir-marriage-legality.v1"
        or legality.get("exact_ck3_build") != "1.19.0.6"
        or legality.get("status") != "available"
        or legality.get("read_only") is not True
        or legality.get("advertised") is not False
        or legality.get("native_revision") != revision
        or not _positive(legality.get("query_sequence"))
        or not _positive(legality.get("root_query_sequence"))
        or not _positive(heir_id)
        or heir_id == played_id
        or not _positive(candidate_character_id)
        or not isinstance(rows, list)
    ):
        raise BridgeUnavailableError("heir marriage lacks same-frame public legality")
    matches = [row for row in rows if isinstance(row, dict) and
               row.get("candidate_character_id") == candidate_character_id]
    if len(matches) != 1:
        raise BridgeUnavailableError("heir marriage candidate is not uniquely legal")
    row = matches[0]
    if (
        row.get("played_character_id") != played_id
        or row.get("subject_character_id") != heir_id
        or not _positive(row.get("recipient_matchmaker_character_id"))
        or row.get("intermediary_character_id") != -1
        or row.get("native_rank") is not None
        or row.get("complete_can_send") is not True
        or row.get("recipient_answer_allows_send") is not True
        or row.get("recipient_answer_status_raw") not in {0, 1}
        or type(row.get("recipient_ai_accept_raw")) is not int
    ):
        raise BridgeUnavailableError("heir marriage row lacks final native legality")
    if _paused(driver)["native_revision"] != revision:
        raise BridgeUnavailableError("heir marriage paused frame changed before submit")
    result = _command(driver, SUBMIT_STEP, {
        "expected_revision": revision,
        "query_sequence": legality["query_sequence"],
        "candidate_character_id": candidate_character_id,
    }, timeout_seconds)
    if (
        result.get("status") != "receipt_pending"
        or result.get("material_result") is not False
        or result.get("pre_native_revision") != revision
        or result.get("played_character_id") != played_id
        or result.get("heir_character_id") != heir_id
        or result.get("candidate_character_id") != candidate_character_id
    ):
        raise BridgeUnavailableError("heir marriage ACK cannot prove an outcome")
    return {"schema": SCHEMA, "schema_version": 1,
            "exact_ck3_build": "1.19.0.6", "advertised": False,
            **result}


def query_observed_first_heir_marriage_result_private_v1(
    driver: object, *, pending: dict[str, object],
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Only bilateral marriage or betrothal on a later frame is material."""
    snapshot = _paused(driver)
    revision = snapshot["native_revision"]
    pre = pending.get("pre_native_revision")
    heir_id = pending.get("heir_character_id")
    candidate_id = pending.get("candidate_character_id")
    if (
        pending.get("schema") != SCHEMA
        or pending.get("status") != "receipt_pending"
        or pending.get("material_result") is not False
        or not _positive(pre) or revision <= pre
        or not _positive(heir_id) or not _positive(candidate_id)
    ):
        raise BridgeUnavailableError("heir marriage needs a later-frame pending receipt")
    result = _command(driver, RESULT_STEP,
                      {"expected_revision": revision}, timeout_seconds)
    status = result.get("status")
    if (
        status not in {"pending", "accepted_pending", "refused", "invalidated",
                       "marriage", "betrothal"}
        or result.get("material_result") is not (status in {"marriage", "betrothal"})
        or result.get("cold_recovery") is not False
        or result.get("pre_native_revision") != pre
        or result.get("post_native_revision") != revision
        or result.get("heir_character_id") != heir_id
        or result.get("candidate_character_id") != candidate_id
    ):
        raise BridgeUnavailableError("heir marriage material readback disagrees with receipt")
    return {"schema": SCHEMA, "schema_version": 1,
            "exact_ck3_build": "1.19.0.6", "advertised": False,
            **result}


def query_observed_first_heir_marriage_cold_result_private_v1(
    driver: object, *, pending: dict[str, object],
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Re-read the pair after a new PID; absent relation remains unresolved."""
    before = _paused(driver)
    heir_id = pending.get("heir_character_id")
    candidate_id = pending.get("candidate_character_id")
    source_date = pending.get("source_date_raw")
    if (
        pending.get("schema") != SCHEMA
        or pending.get("status") != "receipt_pending"
        or pending.get("played_character_id") !=
           before["played_character"]["character_id"]
        or not _positive(heir_id) or not _positive(candidate_id)
        or type(source_date) is not int or source_date < 0
        or type(before.get("date_raw")) is not int
        or before["date_raw"] < source_date
    ):
        raise BridgeUnavailableError("cold heir marriage needs a bound pending pair")
    root = driver._execute_campaign_root_context_v1_query(
        expected_revision=before["revision"])
    partition = root.get("held_title_partition")
    primary = [row for row in partition if isinstance(row, dict)
               and row.get("primary") is True] if isinstance(partition, list) else []
    if (root.get("status") != "available" or len(primary) != 1 or
            primary[0].get("first_heir_character_id") != heir_id or
            _paused(driver)["native_revision"] != before["native_revision"]):
        raise BridgeUnavailableError("cold heir marriage changed first heir or frame")
    result = _command(driver, RESULT_STEP, {
        "expected_revision": before["native_revision"],
        "cold_recovery": 1,
        "heir_character_id": heir_id,
        "candidate_character_id": candidate_id,
        "source_date_raw": source_date,
    }, timeout_seconds)
    status = result.get("status")
    if (
        status not in {"pending", "marriage", "betrothal"}
        or result.get("material_result") is not (status != "pending")
        or result.get("cold_recovery") is not True
        or result.get("pre_native_revision") != 0
        or result.get("post_native_revision") != before["native_revision"]
        or result.get("heir_character_id") != heir_id
        or result.get("candidate_character_id") != candidate_id
    ):
        raise BridgeUnavailableError("cold heir marriage pair readback malformed")
    return {"schema": SCHEMA, "schema_version": 1,
            "exact_ck3_build": "1.19.0.6", "advertised": False,
            "cold_absent_relation_unresolved": status == "pending", **result}
