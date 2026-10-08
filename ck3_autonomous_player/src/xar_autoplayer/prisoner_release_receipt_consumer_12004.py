"""Resolve a retained release ACK from an independent current custody query."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from .environment import write_json_atomic
from .bridge.driver import BridgeUnavailableError
from .bridge.prisoner_retained_target_state_contract_12004 import (
    normalize_prisoner_retained_target_state_12004,
)
from .prisoner_ransom_formal_consumer import _frame, _fresh_private_pump


RECEIPT_STEP = "query-player-prisoner-release-receipt-v1"


def read_release_receipt_private(
    driver: object, *, pending: Mapping[str, object],
) -> dict[str, object]:
    """Read actual freedom separately from transfer/death or an ACK.

    The original accepted offer established player custody. A new target read
    establishes the current postcondition. This does not attribute its cause,
    prove command fees, or repeat submission after a cold restore.
    """
    from .prisoner_release_formal_consumer import _LEDGER, read_release_ledger

    state_dir = driver.state_dir
    ledger = read_release_ledger(state_dir)
    if ledger["pending"] != dict(pending):
        raise BridgeUnavailableError("release pending identity differs from ledger")
    now = driver.take_snapshot()
    actor, native, date = _frame(now)
    target = pending.get("prisoner_character_id")
    if actor != pending.get("player_character_id") or type(target) is not int:
        raise BridgeUnavailableError("release receipt changed its original player/target")
    if type(pending.get("pre_date_raw")) is not int or date < pending["pre_date_raw"]:
        raise BridgeUnavailableError("release receipt precedes its original submit date")
    _fresh_private_pump(driver, date)
    collection = driver.query_player_prisoner_collection_private_v1(
        expected_revision=now["revision"],
        release_material_target_character_id=target,
    )
    try:
        current = normalize_prisoner_retained_target_state_12004(
            collection.get("prisoner_retained_target_state"),
            native_revision=native, date_raw=date,
            player_character_id=actor, target_character_id=target,
        )
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    state = current["custody_state"]
    applied = current["available"] and state == "free"
    terminal = applied or current["available"] and state in {"held_by_other", "dead"}
    status = ("applied" if applied else "transferred" if state == "held_by_other"
              else "dead" if state == "dead" else "pending")
    result = {
        "schema": "xar.ck3.prisoner-release-independent-receipt-12004-v1",
        "status": status, "material_result": applied,
        "postcondition_verified": applied,
        "release_causation_observed": False,
        "command_costs_verified": False,
        "player_character_id": actor, "prisoner_character_id": target,
        "post_native_revision": native, "post_date_raw": date,
        "unavailable_reason": current["unavailable_reason"],
        "current_target_state": current,
        "source_pending": copy.deepcopy(dict(pending)),
        "independent_readback": copy.deepcopy(collection),
    }
    if terminal:
        updated = {"pending": None, "resolved": result}
    else:
        updated_pending = {**copy.deepcopy(dict(pending)),
                           "last_checked_native_revision": native,
                           "last_checked_date_raw": date,
                           "last_receipt": result}
        # Avoid recursively retaining prior last_receipt trees in the next read.
        result["source_pending"].pop("last_receipt", None)
        updated = {"pending": updated_pending, "resolved": ledger.get("resolved")}
    write_json_atomic(state_dir / _LEDGER, updated)
    return result
