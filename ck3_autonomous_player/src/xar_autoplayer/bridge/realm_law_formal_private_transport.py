"""Default-off crown-law observation, typed submit and independent receipt.

The native LAW4/LAW8 source owns final legality, recapture, resource accounting
and successor verification. This module transports an explicitly selected law
and caller budgets; it does not choose a law or equate its ACK with enactment.
"""

from __future__ import annotations

from collections.abc import Mapping
import time
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import (
    private_native_build_identity, private_native_provenance, private_native_readback_matches,
)
from .version_identity import CK3_12002, CK3_12003, CK3_12004


QUERY_STEP = "query-realm-law-crown-action-v1-private"
SUBMIT_STEP = "enact-realm-law-crown-v1-private"
RECEIPT_STEP = "verify-realm-law-crown-v1-private"
READ_SCHEMA = "realm-law-crown-action-private-read-v1"
ACTION_SCHEMA = "realm-law-crown-formal-private-v1"
CURRENCIES = ("gold", "prestige", "piety", "influence", "merit")


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _integer64(value: object) -> bool:
    return type(value) is int and -(1 << 63) <= value < (1 << 63)


def _action_id(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value.encode("utf-8")) <= 63


def _take_snapshot(driver: object) -> dict[str, object]:
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    return reader() if callable(reader) else driver.take_snapshot()


def _paused(driver: object, *, public_revision: int | None = None,
            native_revision: int | None = None) -> dict[str, object]:
    if getattr(driver, "allow_private_realm_law_action", False) is not True:
        raise UnsupportedStepError("private realm-law action is disabled")
    before = _take_snapshot(driver)
    actor = before.get("played_character")
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not _positive(actor.get("character_id"))
            or not _positive(before.get("native_revision"))
            or type(before.get("date_raw")) is not int
            or (public_revision is not None and before.get("revision") != public_revision)
            or (native_revision is not None and before.get("native_revision") != native_revision)
            or private_native_build_identity(before) not in (CK3_12002, CK3_12003, CK3_12004)):
        raise BridgeUnavailableError("private crown-law action requires its exact paused 1.20 frame")
    return before


class _CrownReadStaleFrameError(BridgeUnavailableError):
    """The native frame rejected a read before any law operation ran."""


def _wait_for_new_read_frame(
    driver: object, before: Mapping[str, object], *, deadline: float,
    rejection: _CrownReadStaleFrameError,
) -> dict[str, object]:
    while True:
        fresh = _take_snapshot(driver)
        native_revision = fresh.get("native_revision")
        if _positive(native_revision) and native_revision > before["native_revision"]:
            return _paused(driver, public_revision=fresh.get("revision"))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise rejection
        wait = getattr(driver.state, "wait_for_public_change", None)
        if callable(wait):
            wait(fresh["revision"], remaining)
        else:
            time.sleep(min(0.01, remaining))


def _send(driver: object, before: Mapping[str, object], *, step: str,
          fields: Mapping[str, object], timeout_seconds: float) -> dict[str, object]:
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_id = "law-crown-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": before["played_character"]["character_id"],
        **fields,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private crown-law command_result unavailable")
    if frame.get("ok") is not True:
        if (step == QUERY_STEP and frame.get("ok") is False
                and frame.get("error") == "nonwar private snapshot revision is stale or malformed"):
            raise _CrownReadStaleFrameError(
                "private crown-law native RED: " + frame["error"])
        raise BridgeUnavailableError("private crown-law native RED: " + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    build = private_native_build_identity(before)
    if (not isinstance(envelope, dict) or envelope.get("step") != step
            or envelope.get("accepted") is not True
            or envelope.get("private_build") is not True
            or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"
            or envelope.get("game_version") != build.game_version
            or envelope.get("executable_sha256") != build.executable_sha256
            or envelope.get("read_only") is not (step != SUBMIT_STEP)):
        raise BridgeUnavailableError("private crown-law envelope malformed")
    after = _take_snapshot(driver)
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or after.get("played_character") != before["played_character"]):
        raise BridgeUnavailableError("private crown-law transport crossed actor/date frame")
    return envelope


def _valid_titles(value: object) -> bool:
    if not isinstance(value, dict) or not _positive(value.get("primary_title_id")):
        return False
    titles = value.get("held_titles")
    if not isinstance(titles, list) or not 1 <= len(titles) <= 32:
        return False
    for title in titles:
        if (not isinstance(title, dict) or not _positive(title.get("title_id"))
                or type(title.get("primary")) is not bool
                or not isinstance(title.get("successor_character_ids"), list)
                or len(title["successor_character_ids"]) > 32
                or any(not _positive(successor) for successor in title["successor_character_ids"])):
            return False
    return True


def _valid_observation(value: object, before: Mapping[str, object]) -> bool:
    if (not isinstance(value, dict) or value.get("available") is not True
            or value.get("paused") is not True
            or value.get("snapshot_revision") != before["native_revision"]
            or not _positive(value.get("native_snapshot_revision"))
            or not _positive(value.get("proof_epoch"))
            or value.get("date_raw") != before["date_raw"]
            or value.get("player_character_id") != before["played_character"]["character_id"]
            or value.get("group_key") != "crown_authority"
            or not isinstance(value.get("active_law_key"), str)
            or not _valid_titles(value.get("title_successors"))):
        return False
    resources = value.get("resources")
    if (not isinstance(resources, list) or len(resources) != len(CURRENCIES)
            or any(not isinstance(row, dict) or row.get("currency_key") not in CURRENCIES
                   or not _integer64(row.get("amount_raw")) for row in resources)
            or {row["currency_key"] for row in resources} != set(CURRENCIES)):
        return False
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 24:
        return False
    active = []
    for candidate in candidates:
        if (not isinstance(candidate, dict)
                or not isinstance(candidate.get("law_key"), str)
                or not candidate["law_key"].startswith("crown_authority_")
                or type(candidate.get("is_active")) is not bool
                or type(candidate.get("engine_final_only")) is not bool
                or type(candidate.get("can_enact")) is not bool
                or not isinstance(candidate.get("blocked_reason"), str)):
            return False
        costs = candidate.get("costs")
        if (not isinstance(costs, list) or len(costs) > 6
                or any(not isinstance(cost, dict) or cost.get("currency_key") not in CURRENCIES
                       or not _integer64(cost.get("cost_raw")) or cost["cost_raw"] < 0 for cost in costs)):
            return False
        if candidate["is_active"]:
            active.append(candidate["law_key"])
    return active == [value["active_law_key"]]


def query_realm_law_crown_action_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if not _positive(expected_revision):
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _paused(driver, public_revision=expected_revision)
    deadline = time.monotonic() + float(timeout_seconds)
    try:
        result = _send(driver, before, step=QUERY_STEP, fields={}, timeout_seconds=timeout_seconds)
    except _CrownReadStaleFrameError as rejection:
        before = _wait_for_new_read_frame(driver, before, deadline=deadline, rejection=rejection)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise rejection
        # Only the rejected read is repeated, using an actually published newer
        # native frame. Submission and receipt operations retain their behavior.
        result = _send(driver, before, step=QUERY_STEP, fields={}, timeout_seconds=remaining)
    observation = result.get("observation")
    if (result.get("status") != "available" or result.get("ack") is not None
            or result.get("receipt") is not None or not _valid_observation(observation, before)):
        raise BridgeUnavailableError("private crown-law observation malformed")
    return {
        **observation, "schema": READ_SCHEMA, **private_native_provenance(before),
        "read_only": True, "advertised": False,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": before["revision"],
        "queried_native_revision": before["native_revision"],
    }


def submit_realm_law_crown_private_v1(
    driver: object, *, readback: Mapping[str, object], law_key: str,
    budgets: Mapping[str, int], action_id: str, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if not isinstance(law_key, str) or not law_key.startswith("crown_authority_") or len(law_key) > 95:
        raise ValueError("law_key must identify a crown-authority candidate")
    if (not isinstance(budgets, Mapping)
            or any(key not in CURRENCIES or not _integer64(amount) or amount < 0
                   for key, amount in budgets.items())):
        raise ValueError("budgets must contain supported nonnegative raw currency limits")
    if not _action_id(action_id):
        raise ValueError("action_id must be nonempty and fit the native request ID")
    revision = readback.get("queried_native_revision")
    if not _positive(revision):
        raise ValueError("private crown-law submit requires a queried readback")
    before = _paused(driver, native_revision=revision)
    if (readback.get("schema") != READ_SCHEMA
            or not private_native_readback_matches(before, readback)
            or not _valid_observation(dict(readback), before)):
        raise BridgeUnavailableError("private crown-law submit lacks its observed paused source")
    candidate = next((row for row in readback["candidates"] if row["law_key"] == law_key), None)
    if (candidate is None or candidate["is_active"] is not False
            or candidate["can_enact"] is not True):
        raise BridgeUnavailableError("selected crown law lacks the native final can-enact result")
    # Native final CanEnact can allow an override even when component
    # CanHave/CanPass are false. Do not AND those components into this result.
    result = _send(driver, before, step=SUBMIT_STEP, fields={
        "submitted_request_id": action_id, "group_key": readback["group_key"],
        "law_key": law_key,
        "expected_native_revision": readback["native_snapshot_revision"],
        "expected_proof_epoch": readback["proof_epoch"],
        **{f"budget_{key}_raw": amount for key, amount in budgets.items()},
    }, timeout_seconds=timeout_seconds)
    ack = result.get("ack")
    if (result.get("status") not in {"submitted_verification_pending", "rejected_before_submit"}
            or not isinstance(ack, dict) or ack.get("submitted_request_id") != action_id):
        raise BridgeUnavailableError("private crown-law submit result malformed")
    if result["status"] == "submitted_verification_pending" and (
            ack.get("verification_pending") is not True
            or ack.get("player_character_id") != readback["player_character_id"]
            or ack.get("requested_law_key") != law_key
            or ack.get("group_key") != readback["group_key"]
            or ack.get("pre_public_revision") != revision
            or ack.get("pre_date_raw") != readback["date_raw"]
            or not _valid_titles(ack.get("title_successors"))):
        raise BridgeUnavailableError("private crown-law submit ACK identity malformed")
    return {**ack, "schema": ACTION_SCHEMA, "status": result["status"],
            "material_result": False, **private_native_provenance(before)}


def query_realm_law_crown_receipt_private_v1(
    driver: object, *, expected_revision: int, submitted_request_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if not _positive(expected_revision) or not _action_id(submitted_request_id):
        raise ValueError("private crown-law receipt identity is invalid")
    before = _paused(driver, public_revision=expected_revision)
    result = _send(driver, before, step=RECEIPT_STEP,
                   fields={"submitted_request_id": submitted_request_id}, timeout_seconds=timeout_seconds)
    receipt = result.get("receipt")
    if (result.get("status") not in {"enacted", "failed"} or not isinstance(receipt, dict)
            or receipt.get("submitted_request_id") != submitted_request_id):
        raise BridgeUnavailableError("private crown-law receipt malformed")
    enacted = result["status"] == "enacted"
    if enacted and (
            receipt.get("effective_law_verified") is not True
            or receipt.get("resources_verified") is not True
            or receipt.get("succession_verified") is not True
            or receipt.get("post_public_revision") != before["native_revision"]
            or receipt.get("post_date_raw") != before["date_raw"]
            or not isinstance(receipt.get("effective_law_key"), str)
            or not _valid_titles(receipt.get("title_successors"))):
        raise BridgeUnavailableError("private crown-law enacted receipt lacks material verification")
    return {**receipt, "schema": ACTION_SCHEMA, "status": result["status"],
            "material_result": enacted, **private_native_provenance(before)}
