"""Private selected-option marriage for a verified player child."""

from __future__ import annotations

import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .marriage_matchmaking_private_transport import _require_same_paused_frame
from .nonwar_private_build import private_native_provenance


SUBMIT_STEP = "submit-player-child-matrilineal-marriage-v1-private"
RESULT_STEP = "query-player-child-matrilineal-marriage-result-v1-private"
ALLIANCE_RESULT_STEP = "query-player-child-matrilineal-alliance-result-v1-private"
SCHEMA = "xar.ck3.player-child-matrilineal-private-action.v1"
DEFAULT_SUBMIT_STEP = "submit-player-child-default-marriage-v1-private"
DEFAULT_RESULT_STEP = "query-player-child-default-marriage-result-v1-private"
DEFAULT_ALLIANCE_RESULT_STEP = "query-player-child-default-alliance-result-v1-private"
DEFAULT_SCHEMA = "xar.ck3.player-child-default-private-action.v1"


def _positive(value: object) -> bool:
    return type(value) is int and 0 < value < 2**31


def _paused(driver: object) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, dict) or played.get("alive") is not True
            or not _positive(played.get("character_id"))
            or not _positive(snapshot.get("native_revision"))):
        raise BridgeUnavailableError("child proposal needs a paused living-player frame")
    return snapshot


def _command(driver: object, step: str, payload: dict[str, object],
             timeout_seconds: float) -> dict[str, object]:
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "family-child-action-" + uuid.uuid4().hex
    driver.endpoint.send({"type": "execute_step", "protocol_version": 1,
                          "request_id": request_id, "step": step, **payload})
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("child proposal timed out; outcome unknown")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("child proposal RED: " +
                                     str(frame.get("error") or "unknown"))
    result = frame.get("result")
    if (not isinstance(result, dict) or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("private_build") is not True
            or result.get("advertised") is not False):
        raise BridgeUnavailableError("child proposal response shape changed")
    return result


def submit_player_child_matrilineal_private_v1(
    driver: object, *, legality: dict[str, object], value: dict[str, object],
    timeout_seconds: float = 360.0,
    default_route: bool = False,
) -> dict[str, object]:
    """Queue one same-frame native five-role proposal; ACK is only pending."""
    if type(default_route) is not bool:
        raise ValueError("default_route must be bool")
    permission = ("allow_private_player_child_default_action" if default_route else
                  "allow_private_player_child_matrilineal_action")
    if getattr(driver, permission, False) is not True:
        raise UnsupportedStepError("private player-child proposal disabled")
    selected_option = not default_route
    before = _paused(driver)
    revision = before["native_revision"]
    played_id = before["played_character"]["character_id"]
    subject_id = legality.get("subject_character_id")
    candidate_id = value.get("candidate_character_id")
    rows = legality.get("native_legal_candidates")
    matches = ([row for row in rows if isinstance(row, dict) and
                row.get("candidate_character_id") == candidate_id]
               if isinstance(rows, list) else [])
    row = value.get("row")
    if (legality.get("schema") != "xar.ck3.player-child-marriage-subject.v1"
            or legality.get("status") != "available"
            or legality.get("player_child_verified") is not True
            or legality.get("native_revision") != revision
            or legality.get("played_character_id") != played_id
            or not _positive(subject_id) or not _positive(candidate_id)
            or not _positive(legality.get("query_sequence"))
            or len(matches) != 1
            or value.get("schema") != "xar.ck3.player-child-marriage-value.v1"
            or value.get("status") != "available"
            or value.get("read_only") is not True
            or value.get("advertised") is not False
            or value.get("native_revision") != revision
            or value.get("legality_query_sequence") != legality["query_sequence"]
            or value.get("played_character_id") != played_id
            or value.get("subject_character_id") != subject_id
            or value.get("request_matrilineal_option") is not selected_option
            or not isinstance(row, dict)
            or row.get("actor_character_id") != played_id
            or row.get("heir_character_id") != subject_id
            or row.get("candidate_character_id") != candidate_id
            or row.get("recipient_character_id") !=
                matches[0].get("recipient_matchmaker_character_id")
            or row.get("requested_matrilineal_option") is not selected_option
            or (selected_option and row.get("selected_option_readback") is not True)
            or row.get("matrilineal_option_selected") is not selected_option
            or row.get("effective_matrilineal_if_accepted") is not selected_option
            or row.get("final_legality_sampled") is not True
            or row.get("complete_can_send") is not True
            or row.get("recipient_answer_status_raw") not in {0, 1}
            or type(row.get("recipient_ai_accept_raw")) is not int
            or row["recipient_ai_accept_raw"] <= 0):
        raise BridgeUnavailableError("child proposal lacks selected native final proof")
    _require_same_paused_frame(_paused(driver), before, revision, played_id)
    result = _command(driver, DEFAULT_SUBMIT_STEP if default_route else SUBMIT_STEP, {
        "expected_revision": revision,
        "legality_query_sequence": legality["query_sequence"],
        "subject_character_id": subject_id,
        "candidate_character_id": candidate_id,
    }, timeout_seconds)
    if (result.get("status") != "receipt_pending"
            or result.get("material_result") is not False
            or result.get("pre_native_revision") != revision
            or result.get("played_character_id") != played_id
            or result.get("heir_character_id") != subject_id
            or result.get("candidate_character_id") != candidate_id
            or result.get("recipient_character_id") !=
                matches[0]["recipient_matchmaker_character_id"]
            or result.get("matrilineal_option_selected") is not selected_option):
        raise BridgeUnavailableError("child proposal ACK identity changed; state unknown")
    return {"schema": DEFAULT_SCHEMA if default_route else SCHEMA, "schema_version": 1,
            **private_native_provenance(before), "advertised": False, **result}


def query_player_child_matrilineal_result_private_v1(
    driver: object, *, pending: dict[str, object], cold: bool = False,
    timeout_seconds: float = 360.0,
    default_route: bool = False,
) -> dict[str, object]:
    """Read actual bilateral state on a later frame or after a new PID."""
    if type(default_route) is not bool:
        raise ValueError("default_route must be bool")
    permission = ("allow_private_player_child_default_action" if default_route else
                  "allow_private_player_child_matrilineal_action")
    if getattr(driver, permission, False) is not True:
        raise UnsupportedStepError("private player-child proposal disabled")
    before = _paused(driver)
    selected_option = not default_route
    schema = DEFAULT_SCHEMA if default_route else SCHEMA
    revision = before["native_revision"]
    played_id = before["played_character"]["character_id"]
    subject_id = pending.get("heir_character_id")
    candidate_id = pending.get("candidate_character_id")
    recipient_id = pending.get("recipient_character_id")
    pre = pending.get("pre_native_revision")
    if (pending.get("schema") != schema
            or pending.get("status") != "receipt_pending"
            or pending.get("played_character_id") != played_id
            or pending.get("matrilineal_option_selected") is not selected_option
            or not all(_positive(v) for v in (subject_id, candidate_id, recipient_id))
            or not _positive(pre)
            or (not cold and revision <= pre)
            or (cold and (type(pending.get("source_date_raw")) is not int
                          or before.get("date_raw", -1) < pending["source_date_raw"]))):
        raise BridgeUnavailableError("child proposal result lacks bound pending pair")
    if cold:
        child = driver.query_player_child_marriage_subject_private_v1(
            expected_native_revision=revision, subject_character_id=subject_id)
        if child.get("player_child_verified") is not True:
            raise BridgeUnavailableError("cold child relationship unavailable")
    payload: dict[str, object] = {"expected_revision": revision}
    if cold:
        payload.update({"cold_recovery": 1, "heir_character_id": subject_id,
                        "candidate_character_id": candidate_id,
                        "recipient_character_id": recipient_id,
                        "source_date_raw": pending["source_date_raw"],
                        "matrilineal_option_selected": selected_option})
    result = _command(driver, DEFAULT_RESULT_STEP if default_route else RESULT_STEP,
                      payload, timeout_seconds)
    outbound = result.get("outbound_pending_state")
    if cold and (outbound not in {"active", "absent", "ambiguous", "unavailable"}
                 if result.get("status") == "pending"
                 else outbound != "not_applicable"):
        raise BridgeUnavailableError("cold child proposal outbound state malformed")
    if cold and outbound == "active" and (
            type(result.get("outbound_pending_id")) is not int
            or type(result.get("outbound_pending_age_days")) is not int
            or type(result.get("outbound_pending_ai_reply_cutoff_days")) is not int):
        raise BridgeUnavailableError("cold child proposal pending receipt malformed")
    if (result.get("status") not in {"pending", "accepted_pending", "refused",
                                      "invalidated", "marriage", "betrothal"}
            or (cold and result["status"] in {"accepted_pending", "refused", "invalidated"})
            or result.get("material_result") is not
                (result["status"] in {"marriage", "betrothal"})
            or result.get("cold_recovery") is not cold
            or result.get("post_native_revision") != revision
            or result.get("pre_native_revision") != (0 if cold else pre)
            or result.get("heir_character_id") != subject_id
            or result.get("candidate_character_id") != candidate_id
            or result.get("recipient_character_id") != recipient_id
            or result.get("matrilineal_option_selected") is not selected_option):
        raise BridgeUnavailableError("child proposal result identity changed")
    return {"schema": schema, "schema_version": 1,
            **private_native_provenance(before), "advertised": False,
            "cold_absent_relation_unresolved": cold and result["status"] == "pending",
            **result}


def query_player_child_matrilineal_alliance_private_v1(
    driver: object, *, resolved: dict[str, object],
    timeout_seconds: float = 360.0,
    default_route: bool = False,
) -> dict[str, object]:
    """Read actual bilateral player/recipient alliance after a material pair."""
    if type(default_route) is not bool:
        raise ValueError("default_route must be bool")
    if default_route and getattr(driver, "allow_private_player_child_default_action", False) is not True:
        raise UnsupportedStepError("private player-child default alliance read disabled")
    before = _paused(driver)
    selected_option = not default_route
    schema = DEFAULT_SCHEMA if default_route else SCHEMA
    pending = resolved.get("source_pending")
    if not isinstance(pending, dict):
        raise BridgeUnavailableError("child alliance lacks a durable proposal pair")
    actor = pending.get("played_character_id")
    recipient = pending.get("recipient_character_id")
    subject = pending.get("heir_character_id")
    candidate = pending.get("candidate_character_id")
    if (resolved.get("status") not in {"marriage", "betrothal"}
            or resolved.get("material_result") is not True
            or pending.get("schema") != schema
            or pending.get("matrilineal_option_selected") is not selected_option
            or actor != before["played_character"]["character_id"]
            or not all(_positive(v) for v in (actor, recipient, subject, candidate))
            or resolved.get("heir_character_id") != subject
            or resolved.get("candidate_character_id") != candidate):
        raise BridgeUnavailableError("child alliance pair does not match material result")
    result = _command(driver, DEFAULT_ALLIANCE_RESULT_STEP
                      if default_route else ALLIANCE_RESULT_STEP, {
        "expected_revision": before["native_revision"],
        "played_character_id": actor,
        "recipient_character_id": recipient,
        "heir_character_id": subject,
        "candidate_character_id": candidate,
    }, timeout_seconds)
    status = result.get("alliance_status")
    sides = (result.get("played_has_recipient_alliance"),
             result.get("recipient_has_played_alliance"))
    if (result.get("read_only") is not True
            or result.get("native_revision") != before["native_revision"]
            or result.get("played_character_id") != actor
            or result.get("recipient_character_id") != recipient
            or result.get("heir_character_id") != subject
            or result.get("candidate_character_id") != candidate
            or result.get("relationship_status") != resolved["status"]
            or status not in {"allied", "not_allied", "unknown"}
            or (status == "allied" and sides != (True, True))
            or (status == "not_allied" and sides != (False, False))
            or (status == "unknown" and sides not in
                {(None, None), (True, False), (False, True)})):
        raise BridgeUnavailableError("child alliance bilateral result malformed")
    _require_same_paused_frame(_paused(driver), before,
                               before["native_revision"], actor)
    return {"schema": ("xar.ck3.player-child-default-alliance-result.v1"
                       if default_route else
                       "xar.ck3.player-child-matrilineal-alliance-result.v1"),
            "schema_version": 1, **private_native_provenance(before), **result}
