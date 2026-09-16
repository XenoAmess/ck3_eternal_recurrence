"""Persist one unresolved faction gift across owned CK3 cold restores.

The current private native receipt keeps its ACK in process memory. Until a
recipient/faction recovery read exists, an unresolved entry forbids another
gift submission; a known-empty targeting vector never resolves this entry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .environment import write_json_atomic


_FILENAME = "faction-gift-pending-v1.json"
_SCHEMA = "xar.ck3.faction_gift_pending_v1"


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _hex_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def faction_gift_ledger_path(state_dir: Path) -> Path:
    return Path(state_dir) / "native-session" / _FILENAME


def _empty() -> dict[str, object]:
    return {"schema": _SCHEMA, "format_version": 1, "pending": None,
            "resolved_request_outcomes": {}}


def read_faction_gift_ledger_v1(state_dir: Path) -> dict[str, object]:
    """Read only the scoped ledger; unknown shape is a blocking RED."""
    path = faction_gift_ledger_path(state_dir)
    if not path.is_file():
        return _empty()
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return _validate_ledger(payload)


def _validate_ledger(payload: object) -> dict[str, object]:
    """Validate a candidate in memory before it replaces the durable file."""
    if not isinstance(payload, dict) or set(payload) != {
        "schema", "format_version", "pending", "resolved_request_outcomes"
    } or payload.get("schema") != _SCHEMA or payload.get("format_version") != 1:
        raise ValueError("faction gift pending ledger shape is unknown")
    resolved = payload["resolved_request_outcomes"]
    if not isinstance(resolved, dict) or any(
        not isinstance(request_id, str) or not request_id
        or outcome not in {"applied", "unchanged"}
        for request_id, outcome in resolved.items()
    ):
        raise ValueError("faction gift resolved request outcomes are unknown")
    pending = payload["pending"]
    if pending is not None:
        if not isinstance(pending, dict) or set(pending) != {
            "request_id", "episode_run_id", "source_faction_id",
            "source_round_id", "source_bridge_pid", "source_bridge_creation_date",
            "recipient_character_id", "pre_snapshot_revision",
            "pre_native_snapshot_revision", "pre_date_raw",
            "pre_player_character_id", "pre_player_gold_raw",
            "pre_recipient_opinion_of_player", "pre_gift_opinion_present",
            "pre_source_faction_power_raw", "pre_source_faction_discontent_raw",
            "pre_source_faction_member_character_ids",
            "pre_source_faction_targeting_player",
            "gold_cost_raw", "opinion_delta", "minimum_gold_reserve_raw",
            "checkpoint_sha256_before_submit", "status", "ack",
        }:
            raise ValueError("faction gift pending action shape is unknown")
        if (
            not isinstance(pending["request_id"], str) or not pending["request_id"]
            or pending["request_id"] in resolved
            or not isinstance(pending["episode_run_id"], str)
            or not pending["episode_run_id"]
            or not isinstance(pending["source_round_id"], str)
            or not pending["source_round_id"].startswith("R")
            or not pending["source_round_id"][1:].isdigit()
            or not _positive_int(pending["source_bridge_pid"])
            or not isinstance(pending["source_bridge_creation_date"], str)
            or not pending["source_bridge_creation_date"]
            or any(not _positive_int(pending[field]) for field in (
                "source_faction_id", "recipient_character_id",
                "pre_snapshot_revision", "pre_native_snapshot_revision",
                "pre_player_character_id", "gold_cost_raw", "opinion_delta"
            ))
            or any(not _nonnegative_int(pending[field]) for field in (
                "pre_date_raw", "pre_player_gold_raw",
                "minimum_gold_reserve_raw"
            ))
            or pending["pre_player_gold_raw"] - pending["gold_cost_raw"]
                < pending["minimum_gold_reserve_raw"]
            or any(not isinstance(pending[field], int) or isinstance(pending[field], bool)
                   for field in (
                       "pre_recipient_opinion_of_player",
                       "pre_source_faction_power_raw",
                       "pre_source_faction_discontent_raw",
                   ))
            or pending["pre_gift_opinion_present"] is not False
            or pending["pre_source_faction_targeting_player"] is not True
            or not isinstance(pending["pre_source_faction_member_character_ids"], list)
            or any(not _positive_int(value) for value in pending["pre_source_faction_member_character_ids"])
            or pending["recipient_character_id"] not in pending["pre_source_faction_member_character_ids"]
            or not _hex_digest(pending["checkpoint_sha256_before_submit"])
            or pending["status"] not in {
                "submission_started_unconfirmed", "submitted_verification_pending",
                "restore_requery_required"
            }
            or (pending["ack"] is not None and not isinstance(pending["ack"], dict))
        ):
            raise ValueError("faction gift pending action facts are incomplete")
    return payload


def begin_faction_gift_submission_v1(
    state_dir: Path, *, request_id: str, episode_run_id: str,
    source_round_id: str, source_bridge_pid: int,
    source_bridge_creation_date: str,
    observation: Mapping[str, object], minimum_gold_reserve_raw: int,
    checkpoint_sha256_before_submit: str,
) -> dict[str, object]:
    """Durably mark an action uncertain before the native one-shot send."""
    ledger = read_faction_gift_ledger_v1(state_dir)
    if ledger["pending"] is not None:
        raise ValueError("one faction gift is already unresolved")
    if not isinstance(request_id, str) or not request_id or request_id in ledger["resolved_request_outcomes"]:
        raise ValueError("faction gift request identity is missing or already resolved")
    if not isinstance(episode_run_id, str) or not episode_run_id:
        raise ValueError("faction gift episode identity is missing")
    preview = observation.get("gift_preview")
    if not isinstance(preview, Mapping):
        raise ValueError("faction gift preview is missing")
    pending = {
        "request_id": request_id,
        "episode_run_id": episode_run_id,
        "source_round_id": source_round_id,
        "source_bridge_pid": source_bridge_pid,
        "source_bridge_creation_date": source_bridge_creation_date,
        "source_faction_id": observation.get("queried_source_faction_id"),
        "recipient_character_id": observation.get("recipient_character_id"),
        "pre_snapshot_revision": observation.get("snapshot_revision"),
        "pre_native_snapshot_revision": observation.get("native_snapshot_revision"),
        "pre_date_raw": observation.get("observed_date_raw"),
        "pre_player_character_id": observation.get("player_character_id"),
        "pre_player_gold_raw": observation.get("player_gold_raw"),
        "pre_recipient_opinion_of_player": observation.get("recipient_opinion_of_player"),
        "pre_gift_opinion_present": observation.get("gift_opinion_present"),
        "pre_source_faction_power_raw": observation.get("source_faction_power_raw"),
        "pre_source_faction_discontent_raw": observation.get("source_faction_discontent_raw"),
        "pre_source_faction_member_character_ids": observation.get("source_faction_member_character_ids"),
        "pre_source_faction_targeting_player": observation.get("source_faction_targeting_player"),
        "gold_cost_raw": preview.get("gold_cost_raw"),
        "opinion_delta": preview.get("opinion_delta"),
        "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        "checkpoint_sha256_before_submit": checkpoint_sha256_before_submit,
        "status": "submission_started_unconfirmed",
        "ack": None,
    }
    candidate = _validate_ledger({**ledger, "pending": pending})
    path = faction_gift_ledger_path(state_dir)
    write_json_atomic(path, candidate)
    return read_faction_gift_ledger_v1(state_dir)


def mark_faction_gift_ack_pending_v1(
    state_dir: Path, *, request_id: str, ack: Mapping[str, object]
) -> dict[str, object]:
    """ACK records submission uncertainty; it never proves game effect."""
    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger["pending"]
    if not isinstance(pending, dict) or pending["request_id"] != request_id:
        raise ValueError("faction gift ACK lacks the unresolved action identity")
    if (ack.get("request_id") != request_id
            or ack.get("status") != "submitted_verification_pending"
            or ack.get("verification_pending") is not True
            or ack.get("source_faction_id") != pending["source_faction_id"]
            or ack.get("recipient_character_id") != pending["recipient_character_id"]):
        raise ValueError("faction gift ACK is not a matching pending submission")
    updated = {**pending, "status": "submitted_verification_pending", "ack": dict(ack)}
    write_json_atomic(faction_gift_ledger_path(state_dir), {**ledger, "pending": updated})
    return read_faction_gift_ledger_v1(state_dir)


def mark_faction_gift_restore_requery_v1(state_dir: Path, *, request_id: str) -> dict[str, object]:
    """Keep an old action blocked until an independent exact native read."""
    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger["pending"]
    if not isinstance(pending, dict) or pending["request_id"] != request_id:
        raise ValueError("restored faction gift request identity differs")
    write_json_atomic(faction_gift_ledger_path(state_dir), {
        **ledger, "pending": {**pending, "status": "restore_requery_required"}
    })
    return read_faction_gift_ledger_v1(state_dir)


def complete_faction_gift_after_independent_receipt_v1(
    state_dir: Path, *, request_id: str, receipt: Mapping[str, object]
) -> dict[str, object]:
    """Only a matching independent game receipt can close the action."""
    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger["pending"]
    if not isinstance(pending, dict) or pending["request_id"] != request_id:
        raise ValueError("faction gift receipt has no matching unresolved action")
    if not (
        receipt.get("schema_version") == 1
        and receipt.get("request_id") == request_id
        and receipt.get("status") in {"mitigated", "left"}
        and receipt.get("postcondition_verified") is True
        and receipt.get("mitigation_applied") is True
        and receipt.get("source_faction_id") == pending["source_faction_id"]
        and receipt.get("recipient_character_id") == pending["recipient_character_id"]
        and receipt.get("player_character_id") == pending["pre_player_character_id"]
        and _positive_int(receipt.get("post_snapshot_revision"))
        and receipt["post_snapshot_revision"] > pending["pre_snapshot_revision"]
        and _positive_int(receipt.get("post_native_snapshot_revision"))
        and receipt["post_native_snapshot_revision"] > pending["pre_native_snapshot_revision"]
        and receipt.get("post_observed_date_raw") == pending["pre_date_raw"]
        and receipt.get("post_player_gold_raw") == (
            pending["pre_player_gold_raw"] - pending["gold_cost_raw"]
        )
        and receipt.get("post_gift_opinion_present") is True
        and receipt.get("post_gift_opinion_modifier_value") == pending["opinion_delta"]
    ):
        raise ValueError("faction gift receipt lacks matching independent post-state")
    updated = {**ledger, "pending": None,
               "resolved_request_outcomes": {
                   **ledger["resolved_request_outcomes"], request_id: "applied"
               }}
    write_json_atomic(faction_gift_ledger_path(state_dir), updated)
    return read_faction_gift_ledger_v1(state_dir)


def resolve_faction_gift_after_cold_native_query_v1(
    state_dir: Path, *, request_id: str, recovery: Mapping[str, object]
) -> dict[str, object]:
    """Retire one old identity only after material new-process readback.

    `unchanged` permits a newly selected action with a different request ID;
    the old one-shot ID must never be sent again. Unknown leaves it pending.
    """
    from .faction_gift_cold_recovery_contract_v1 import (
        evaluate_faction_gift_cold_recovery_v1,
    )

    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger["pending"]
    if not isinstance(pending, dict) or pending["request_id"] != request_id:
        raise ValueError("cold faction gift query lacks matching pending identity")
    result = evaluate_faction_gift_cold_recovery_v1(pending, recovery)
    if result["status"] not in {"applied", "unchanged"}:
        return result
    updated = {**ledger, "pending": None,
               "resolved_request_outcomes": {
                   **ledger["resolved_request_outcomes"],
                   request_id: result["status"],
               }}
    write_json_atomic(faction_gift_ledger_path(state_dir), updated)
    return {**result, "ledger": read_faction_gift_ledger_v1(state_dir)}
