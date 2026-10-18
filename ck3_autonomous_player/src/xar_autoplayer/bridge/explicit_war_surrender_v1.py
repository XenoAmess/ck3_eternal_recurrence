"""Explicit player surrender: native permission, never an automatic policy.

The existing fixed surrender-war-N native command still performs its original
owning-thread/frame/participant/primary-leader/context/validator checks. This
adapter only admits an explicit public request from an exact same-frame query.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid

from .driver import BridgeUnavailableError
from .rite_creation_action_private_v1 import _binding, _machine_id, _save_exclusive


def explicit_surrender_evidence(snapshot: dict, war_id: int, revision: int) -> dict:
    """Require the actual native option; score/CB/duration are not policy gates."""
    if type(war_id) is not int or not 1 <= war_id <= 0x7FFFFFFF:
        raise ValueError("war_id must be a positive full native WarID")
    bound = _binding(snapshot, revision)  # Exact .4, alive/paused/map, durable scope.
    wars = snapshot.get("active_wars")
    wars = [w for w in wars if isinstance(w, dict) and w.get("war_id") == war_id] if isinstance(wars, list) else []
    rows = snapshot.get("war_termination_options")
    rows = [r for r in rows if isinstance(r, dict) and r.get("war_id") == war_id] if isinstance(rows, list) else []
    if len(wars) != 1 or len(rows) != 1:
        raise BridgeUnavailableError("explicit surrender requires one active full WarID and one fresh query")
    war, options = wars[0], rows[0]
    expected = {"queried_snapshot_id": snapshot.get("snapshot_id"),
        "queried_revision": revision, "queried_native_revision": bound["native_revision"],
        "queried_connection_generation": bound["connection_generation"],
        "episode_run_id": bound["episode_run_id"]}
    if (not isinstance(snapshot.get("snapshot_id"), str) or not snapshot["snapshot_id"]
            or any(options.get(k) != v for k, v in expected.items())
            or type(options.get("query_sequence")) is not int
            or not 1 <= options["query_sequence"] <= (1 << 64) - 1):
        raise BridgeUnavailableError("explicit surrender query is not bound to this paused frame")
    side = war.get("player_side")
    if (side not in ("attacker", "defender") or war.get("player_is_primary_war_leader") is not True
            or options.get("player_side") != side or options.get("player_is_primary_war_leader") is not True
            or options.get("player_relative_war_score") != war.get("player_relative_war_score")):
        raise BridgeUnavailableError("explicit surrender lacks the current player primary-leader identity")
    values = options.get("options")
    surrender = values.get("surrender") if isinstance(values, dict) else None
    if (not isinstance(surrender, dict)
            or surrender.get("outcome") != {"attacker": "attacker_defeat", "defender": "attacker_victory"}[side]
            or surrender.get("hostage_variant") != "none"
            or any(surrender.get(k) is not True for k in ("context_constructed", "native_validator_passed",
                "available", "auto_accept_observable", "auto_accept"))
            or not isinstance(surrender.get("recipient_response"), dict)):
        raise BridgeUnavailableError("explicit surrender lacks original native validator and automatic acceptance")
    # Recipient response and CB terms may remain unavailable. Neither is invented
    # from auto_accept, a score, or the player's authorization to surrender.
    return {"variant": "explicit_player_request", "binding": bound,
        "war": deepcopy(war), "options": deepcopy(options), "surrender": deepcopy(surrender)}


def _claim_path(driver: object, snapshot: dict, war_id: int) -> tuple[Path, dict]:
    bound = _binding(snapshot, snapshot["revision"])
    identity = {"played_character_id": bound["played_character_id"], "war_id": war_id}
    if "intent_scope" in bound:
        identity["managed_campaign_intent_scope"] = deepcopy(bound["intent_scope"])
    else:
        identity["episode_run_id"] = bound["episode_run_id"]
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return driver._native_driver_state_path().parent / "explicit-war-surrender-intents" / (key + ".claim.json"), identity


def reject_existing_explicit_surrender(driver: object, snapshot: dict, war_id: int) -> None:
    # Automatic execute_step keeps its original policy. An explicit unknown send
    # cannot subsequently be replayed by that policy or by a new request/revision.
    if getattr(driver, "state_dir", None) is None:
        return
    folder = driver._native_driver_state_path().parent / "explicit-war-surrender-intents"
    if folder.exists() and _claim_path(driver, snapshot, war_id)[0].exists():
        raise BridgeUnavailableError("explicit surrender already claimed for this player/episode/full WarID; no retry")


def reserve_explicit_surrender(driver: object, snapshot: dict, evidence: dict) -> dict:
    claim, identity = _claim_path(driver, snapshot, evidence["war"]["war_id"])
    claim.parent.mkdir(parents=True, exist_ok=True)
    request_id = "explicit-surrender-" + uuid.uuid4().hex
    record = {"schema": "xar.ck3-explicit-surrender-once.v1", "machine_id": _machine_id(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "request_id": request_id,
        "identity": identity, "binding": evidence["binding"], "query": evidence["options"],
        "status": "claimed_result_unknown_no_retry", "automatic_retry": False}
    try:
        _save_exclusive(claim, record)  # Exclusive creation + flush/fsync BEFORE send.
    except FileExistsError as error:
        raise BridgeUnavailableError("explicit surrender already claimed; no retry") from error
    return {"request_id": request_id, "claim_path": str(claim),
        "native_result_path": str(claim.with_suffix(".native-result.json")),
        "packet_path": str(claim.with_suffix(".packet.bin")), "automatic_retry": False}
