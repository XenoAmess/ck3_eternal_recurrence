"""Submit one queried release offer; its queue ACK leaves freedom unverified."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance
from .prisoner_negotiated_preview_contract_12003 import (
    normalize_prisoner_negotiated_preview_12003, release_option_mask_12003,
)
from .prisoner_release_preview_contract_12003 import (
    normalize_prisoner_release_preview_12003,
)


STEP = "submit-player-prisoner-release-private-v1"
_QUERY_STEP = "query-player-prisoner-collection-private-v1"
_ORDINAL_PREFIX = _QUERY_STEP + "-ransom-ordinal-"


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _selected_ordinal(step: object) -> int:
    if step == _QUERY_STEP:
        return 0
    if isinstance(step, str) and step.startswith(_ORDINAL_PREFIX):
        suffix = step[len(_ORDINAL_PREFIX):]
        if suffix.isascii() and suffix.isdecimal():
            ordinal = int(suffix)
            if 1 <= ordinal <= 63 and suffix == str(ordinal):
                return ordinal
    raise BridgeUnavailableError("release collection lacks its queried prisoner ordinal")


def submit_player_prisoner_release_private_v1(
    driver: object, *, collection: Mapping[str, object],
    prisoner_character_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Consume the selected same-frame typed offer without choosing new terms."""
    if getattr(driver, "allow_private_prisoner_ransom_action", False) is not True:
        raise UnsupportedStepError("private prisoner release action is disabled")
    before = driver.take_snapshot()
    played = before.get("played_character")
    native_revision = before.get("native_revision")
    value = collection.get("player_prisoner_collection")
    rows = value.get("prisoners") if isinstance(value, Mapping) else None
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or not isinstance(played, Mapping)
            or not _positive(played.get("character_id"))
            or not _positive(native_revision)
            or not _positive(prisoner_character_id)
            or collection.get("status") != "available"
            or collection.get("snapshot_revision") != native_revision
            or not _positive(collection.get("query_sequence"))
            or not isinstance(value, Mapping)
            or value.get("played_character_id") != played["character_id"]
            or value.get("date_raw") != before.get("date_raw")
            or value.get("collection_complete") is not True
            or not isinstance(rows, list)):
        raise BridgeUnavailableError("release submit lacks a complete current paused collection")
    ordinal = _selected_ordinal(collection.get("step"))
    matches = [row for row in rows if isinstance(row, Mapping)
               and row.get("prisoner_character_id") == prisoner_character_id]
    if (len(matches) != 1 or ordinal >= len(rows)
            or rows[ordinal] is not matches[0]
            or matches[0].get("source_ordinal") != ordinal):
        raise BridgeUnavailableError("release prisoner differs from the queried collection row")
    row = matches[0]
    if (row.get("collection_owner_character_id") != played["character_id"]
            or row.get("jailer_character_id") != played["character_id"]
            or row.get("custody_relation_verified") is not True):
        raise BridgeUnavailableError("release prisoner lacks current player custody")
    selected_keys: list[str] = []
    mask = 0
    has_keys = "queried_release_option_keys" in collection
    has_mask = "queried_release_option_mask_bits" in collection
    if has_keys != has_mask:
        raise BridgeUnavailableError("release collection lacks its complete queried option terms")
    try:
        if has_keys:
            selected_keys = collection["queried_release_option_keys"]
            mask = release_option_mask_12003(selected_keys)
            if (type(collection["queried_release_option_mask_bits"]) is not int
                    or collection["queried_release_option_mask_bits"] != mask):
                raise ValueError("release query keys differ from its option mask")
            preview = normalize_prisoner_negotiated_preview_12003(
                row.get("negotiated_release_preview"),
                native_revision=native_revision, date_raw=before.get("date_raw"),
                player_character_id=played["character_id"],
                prisoner_character_id=prisoner_character_id,
                requested_option_mask_bits=mask,
            )
        else:
            preview = normalize_prisoner_release_preview_12003(
                row.get("unconditional_release_preview"),
                native_revision=native_revision, date_raw=before.get("date_raw"),
                player_character_id=played["character_id"],
                prisoner_character_id=prisoner_character_id,
            )
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    acceptance = preview.get("acceptance")
    if (preview.get("status") != "available"
            or preview.get("proof_epoch") != collection.get("observation_revision")
            or preview.get("can_send") is not True
            or not isinstance(acceptance, Mapping)
            or not (acceptance.get("auto_accept") is True
                    or acceptance.get("would_accept_now") is True)):
        raise BridgeUnavailableError("release prisoner lacks a currently accepted native offer")
    provenance = private_native_provenance(before)
    request_id = "prisoner-release-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
        "release_query_sequence": collection["query_sequence"],
        "prisoner_character_id": prisoner_character_id,
        "release_option_mask_bits": mask,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("private release submission is unresolved after timeout")
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private release command result is malformed")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(f"private release native RED: {frame.get('error')!r}")
    if frame.get("result") != {"step": STEP, "accepted": True,
                              "status": "submitted_verification_pending"}:
        raise BridgeUnavailableError("private release ACK is not a material result")
    return {
        **provenance,
        "schema": "xar.ck3.prisoner-release-private-action.v1",
        "status": "submitted_verification_pending", "material_result": False,
        "advertised": False, "pre_native_revision": native_revision,
        "pre_date_raw": before["date_raw"],
        "player_character_id": played["character_id"],
        "prisoner_character_id": prisoner_character_id,
        "release_query_sequence": collection["query_sequence"],
        "selected_option_keys": list(selected_keys), "release_option_mask_bits": mask,
        "costs": preview["costs"], "acceptance": preview["acceptance"],
        "request_id": request_id,
    }
