"""Private typed ransom submit. A native queue ACK is never a release receipt."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError


STEP = "submit-player-prisoner-ransom-private-v1"


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def submit_player_prisoner_ransom_private_v1(
    driver: object, *, collection: Mapping[str, object],
    prisoner_character_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Use exactly the latest same-frame native quote for one full prisoner ID."""
    if getattr(driver, "allow_private_prisoner_ransom_action", False) is not True:
        raise UnsupportedStepError("private prisoner ransom action is disabled")
    before = driver.take_snapshot()
    played = before.get("played_character")
    native_revision = before.get("native_revision")
    collection_value = collection.get("player_prisoner_collection")
    rows = (collection_value.get("prisoners")
            if isinstance(collection_value, Mapping) else None)
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or not isinstance(played, Mapping)
            or not _positive(played.get("character_id"))
            or not _positive(native_revision)
            or not _positive(prisoner_character_id)
            or collection.get("status") != "available"
            or collection.get("snapshot_revision") != native_revision
            or not _positive(collection.get("query_sequence"))
            or not isinstance(collection_value, Mapping)
            or collection_value.get("played_character_id") != played["character_id"]
            or collection_value.get("date_raw") != before.get("date_raw")
            or collection_value.get("collection_complete") is not True
            or not isinstance(rows, list)):
        raise BridgeUnavailableError("ransom submit lacks a complete current paused collection")
    matches = [row for row in rows if isinstance(row, Mapping)
               and row.get("prisoner_character_id") == prisoner_character_id]
    if len(matches) != 1:
        raise BridgeUnavailableError("ransom prisoner is not a unique current collection row")
    row = matches[0]
    quote = row.get("ransom_quote_preview")
    if (row.get("jailer_character_id") != played["character_id"]
            or row.get("custody_relation_verified") is not True
            or not isinstance(quote, Mapping)
            or quote.get("status") != "available"
            or quote.get("definition_key") != "ransom_interaction"
            or quote.get("jailer_character_id") != played["character_id"]
            or quote.get("prisoner_character_id") != prisoner_character_id
            or not _positive(quote.get("payer_character_id"))
            or quote.get("selected_option") not in ("gold", "current_gold")
            or quote.get("can_send") is not True
            or quote.get("would_accept_now") is not True
            or quote.get("recipient_answer_status_raw") not in (0, 1)
            or not _positive(quote.get("quoted_gold_raw"))
            or quote.get("raw_scale") != 100_000
            or quote.get("native_revision") != native_revision
            or quote.get("date_raw") != before.get("date_raw")):
        raise BridgeUnavailableError("ransom prisoner lacks an exact native final gold offer")
    request_id = "prisoner-ransom-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
        "quote_query_sequence": collection["query_sequence"],
        "prisoner_character_id": prisoner_character_id,
        "payer_character_id": quote["payer_character_id"],
        "quoted_gold_raw": quote["quoted_gold_raw"],
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("private ransom submission is unresolved after timeout")
    if (not isinstance(frame, dict)
            or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private ransom command result is malformed")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            f"private ransom native RED: {frame.get('error')!r}")
    result = frame.get("result")
    if (not isinstance(result, dict)
            or result != {"step": STEP, "accepted": True,
                          "status": "submitted_verification_pending"}):
        raise BridgeUnavailableError("private ransom ACK is not a material result")
    return {
        "schema": "xar.ck3.prisoner-ransom-private-action.v1",
        "status": "submitted_verification_pending",
        "material_result": False,
        "advertised": False,
        "pre_native_revision": native_revision,
        "pre_date_raw": before["date_raw"],
        "player_character_id": played["character_id"],
        "prisoner_character_id": prisoner_character_id,
        "payer_character_id": quote["payer_character_id"],
        "selected_option": quote["selected_option"],
        "quoted_gold_raw": quote["quoted_gold_raw"],
        "request_id": request_id,
    }
