"""Completed successor UI checkpoint lineage; no pending-state migration.

No game command or MCP registration lives here. A saved JSON anchor is evidence.
Only the canonical App's actual native driver can issue a typed retirement plan.
The owner consumer archives and reads back exact old bytes before retiring the
canonical resolved record; _checked and all action once markers stay intact.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from . import successor_ui_pending_ledger_v1 as journal
from .strategy import normalize_ordinary_campaign_goal_v1

SCHEMA = "xar.ck3.successor-ui-completed-checkpoint/v1"
COMPLETION_FILE = "successor-ui-completed-checkpoint-v1.json"
_SEAL = object()
_CHECKPOINT = ("sha256", "size", "date_raw", "history_index", "episode_character_id", "episode_run_id")


def _json(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > journal.LIMIT:
        raise ValueError("completed successor checkpoint evidence exceeds its small bound")
    return encoded


def _same_checkpoint(left, right):
    return (isinstance(left, Mapping) and isinstance(right, Mapping)
            and all(left.get(key) == right.get(key) for key in _CHECKPOINT))


def _observe_old_game_exit_v1(old):
    """Prove only this bound old Windows PID ended; unknown is not absence.

    _process_identity's None has no source tag. Re-use the existing complete
    Toolhelp enumeration only for that case: it raises on Snapshot/First/Next
    failures and returns only after ERROR_NO_MORE_FILES. No image/time query
    failure or partial identity is interpreted as a different process birth.
    """
    from .runtime import _process_identity
    if (type(old.get("pid")) is not int or old["pid"] <= 0
            or not isinstance(old.get("creation_date"), str) or not old["creation_date"].strip()
            or old["creation_date"].strip().lower() in {"none", "null", "unknown"}):
        raise ValueError("bound old Game process identity unavailable")
    try:
        previous = _process_identity(old["pid"])
    except Exception as error:
        raise ValueError("old Game process identity unavailable") from error
    observed = datetime.now(timezone.utc).isoformat()
    if isinstance(previous, Mapping):
        birth = previous.get("creation_date")
        if (previous.get("pid") != old["pid"] or not isinstance(birth, str)
                or not birth.strip() or birth.strip().lower() in {"none", "null", "unknown"}):
            raise ValueError("old Game process identity unavailable; birth is not proven")
        if birth == old["creation_date"]:
            raise ValueError("original Game process has not exited; no completed retirement")
        return {"status": "old_birth_replaced", "pid": old["pid"], "observed_at_utc": observed,
            "source": "runtime._process_identity", "current_creation_date": birth}
    if previous is not None or os.name != "nt":
        raise ValueError("old Game process absence unavailable")
    from .environment import _toolhelp_process_entries
    try:
        entries = _toolhelp_process_entries()
    except Exception as error:
        raise ValueError("old Game process absence unavailable: complete Toolhelp enumeration failed") from error
    if (not isinstance(entries, list) or not entries
            or any(not isinstance(entry, Mapping) or type(entry.get("pid")) is not int or entry["pid"] < 0
                   for entry in entries)):
        raise ValueError("old Game process absence unavailable: incomplete process enumeration")
    if any(entry["pid"] == old["pid"] for entry in entries):
        raise ValueError("old Game process identity unavailable: PID still present without a known birth")
    return {"status": "old_pid_absent", "pid": old["pid"], "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "environment._toolhelp_process_entries", "complete_enumeration": True}


def _completion(ledger):
    """Re-run the original full/title and Close checks on retained small files."""
    if not isinstance(ledger, journal.SuccessorUIPendingLedger):
        raise TypeError("completion requires the original typed successor ledger")
    value, pin = ledger._checked()
    if value["status"] != "resolved":
        raise ValueError("only independently resolved successor UI can anchor a checkpoint")
    resolved = value.get("resolved_frame")
    transition = value["transition"]
    continuation = transition.get("timeline_blocker_continuation", {})
    if not isinstance(resolved, dict) or any(key not in resolved for key in journal.FRAME):
        raise ValueError("completed successor record lacks its independent resolved frame")
    intent_path = ledger._intent_path()
    intent_pin = None
    if intent_path.exists():
        intent, intent_pin = journal._read(intent_path)
        result = intent.get("result")
        if (intent.get("status") != "verified"
                or intent.get("machine_id") != ledger.machine_id
                or intent.get("source_epoch") != ledger.epoch
                or intent.get("game_identity") != ledger.game
                or intent.get("transition_sha256") != value["transition_sha256"]
                or intent.get("independent_post_frame") != resolved
                or continuation.get("status") != "materially_cleared"
                or continuation.get("close_result") != result
                or ledger.close_validator(result, starting_date_raw=intent["frame"]["date_raw"],
                    successor_character_id=transition["successor_character_id"]) is not None
                or any(resolved[key] != result.get(ending) for key, ending in (
                    ("revision", "ending_revision"), ("native_revision", "ending_native_revision"),
                    ("date_raw", "ending_date_raw")))):
            raise ValueError("completed successor Close lacks its original verified postcondition")
    elif (continuation.get("status") != "already_clear"
            or ledger.timeline_classifier(continuation.get("initial_query")) != "already_clear"):
        raise ValueError("completed successor UI lacks its original independent clear query")
    if (resolved.get("bridge_pid") != ledger.game["pid"]
            or resolved.get("actor_character_id") != transition["successor_character_id"]
            or resolved.get("episode_run_id") != transition["episode_run_id"]):
        raise ValueError("resolved successor frame changed its original episode")
    return value, pin, intent_pin


def capture_completed_checkpoint_v1(ledger, *, save_result, snapshot):
    """Project the original material SAVE and its driver replace receipt.

    The canonical App calls this only after its real driver SAVE has returned.
    It adds no snapshot/capability query and never hashes a SAVE or full Driver.
    The returned JSON is not a new owner binding or a submission permission.
    """
    value, pin, intent_pin = _completion(ledger)
    checkpoint = save_result.get("checkpoint", {})
    receipt = save_result.get("driver_state_replace_receipt", {})
    attempt = receipt.get("attempt_binding", {})
    session = receipt.get("recorded_session_binding", {})
    goal = normalize_ordinary_campaign_goal_v1(snapshot.get("campaign_goal"))
    current = journal.frame(snapshot)
    if (save_result.get("step") != "save-checkpoint" or save_result.get("accepted") is not True
            or save_result.get("materialization", {}).get("available") is not True
            or checkpoint.get("status") != "saved" or checkpoint.get("name") != "xar_checkpoint.ck3"
            or checkpoint.get("strategy") != "native-autosave-command-v1"
            or type(checkpoint.get("size")) is not int or checkpoint["size"] <= 0
            or type(checkpoint.get("history_index")) is not int or checkpoint["history_index"] <= 0
            or not isinstance(checkpoint.get("sha256"), str) or len(checkpoint["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in checkpoint["sha256"])
            or receipt.get("scope") != "WRITE_REPLACE_RETURNED_NOT_FSYNC"
            or receipt.get("status") != "replaced" or receipt.get("write_replace_returned") is not True
            or receipt.get("save_binding_verified") is not True
            or receipt.get("checkpoint") != checkpoint
            or receipt.get("save_history_index") != checkpoint["history_index"]
            or type(receipt.get("encoded_history_rows")) is not int
            or receipt["encoded_history_rows"] < checkpoint["history_index"]
            or any(attempt.get(key) != session.get(key) for key in (
                "pipe_name", "bridge_pid", "episode_character_id", "episode_run_id"))
            or not isinstance(attempt.get("pipe_name"), str) or not attempt["pipe_name"]
            or attempt.get("bridge_pid") != ledger.game["pid"]
            or attempt.get("episode_character_id") != checkpoint.get("episode_character_id")
            or attempt.get("episode_run_id") != checkpoint.get("episode_run_id")
            or attempt.get("succession_lifecycle") != value["verification"]["succession_lifecycle"]
            or checkpoint.get("succession_lifecycle") != attempt.get("succession_lifecycle")
            or normalize_ordinary_campaign_goal_v1(attempt.get("campaign_goal")) != goal
            or normalize_ordinary_campaign_goal_v1(value.get("campaign_goal")) != goal
            or checkpoint.get("episode_character_id") != current["actor_character_id"]
            or checkpoint.get("episode_run_id") != current["episode_run_id"]
            or checkpoint.get("date_raw") != current["date_raw"]
            or current["bridge_pid"] != ledger.game["pid"]
            or current["date_raw"] < value["resolved_frame"]["date_raw"]
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None):
        raise ValueError("completed successor checkpoint lacks its actual paired driver SAVE receipt")
    body = {"schema": SCHEMA, "machine_id": ledger.machine_id, "source_epoch": ledger.epoch,
        "game_identity": deepcopy(ledger.game), "ledger_sha256": pin,
        "transition_sha256": value["transition_sha256"], "close_intent_sha256": intent_pin,
        "campaign_goal": goal, "checkpoint": deepcopy(checkpoint),
        "save_frame": current,
        "save_observation": {**{key: deepcopy(snapshot.get(key)) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_character_id", "episode_run_id", "campaign_goal",
            "paused", "map_ready", "one_life_terminal", "one_life_terminal_reason",
            "episode_identity_pending", "active_event", "pending_character_interaction")},
            "diagnostics": {key: deepcopy(snapshot["diagnostics"].get(key)) for key in journal.FRAME[:2]},
            "played_character": {key: deepcopy(snapshot["played_character"].get(key)) for key in ("character_id", "alive")}},
        "driver_state_replace_receipt": deepcopy(receipt),
        "action_replay_authorized": False}
    _json(body)
    return body


@dataclass(frozen=True, slots=True)
class NativeColdCheckpointProjectionV1:
    """Issued only inside the actual driver's accepted cold binding branch."""
    driver: object
    body: bytes
    seal: object


@dataclass(frozen=True, slots=True)
class NativeColdCheckpointLineageV1:
    """An in-process observation; there is deliberately no JSON constructor."""
    owner: object
    body: bytes
    projection: NativeColdCheckpointProjectionV1
    seal: object


@dataclass(frozen=True, slots=True)
class ResolvedCheckpointRetirementV1:
    """An owner-bound archive plan, never an action or generic migration grant."""
    owner: object
    ledger_path: Path
    ledger_sha256: str
    archive_name: str
    evidence: bytes
    seal: object


def capture_native_cold_projection_v1(driver, *, snapshot):
    """Retain the original cold native frame and actual adopted driver fields.

    Called by the successful, persisted _bind_episode_from_playable_snapshot
    branch. This is the backend's native-frame/episode projection, not a new
    native read or a snapshot reconstructed from a later command summary.
    """
    from .bridge.native_driver import NativeHeadlessGameplayDriver, _checkpoint_history_index, _proven_restore_lineage_row
    from .runtime import _process_identity
    if not isinstance(driver, NativeHeadlessGameplayDriver):
        raise TypeError("cold projection requires the actual native driver")
    with driver._driver_state_lock:
        checkpoint = deepcopy(driver._last_checkpoint)
        history = driver._command_history
        index = _checkpoint_history_index(checkpoint, history)
        if (driver._driver_state_restored is not True or driver._driver_state_restore_kind != "cold_checkpoint"
                or driver._episode_binding_state != "active_resumed" or driver._cold_candidate_rejection is not None
                or driver._pending_cold_candidate is not None or driver._driver_state_error is not None
                or index is None or len(history) <= index
                or not _proven_restore_lineage_row(history[-1], checkpoint)):
            raise ValueError("native driver has no completed exact cold checkpoint lineage")
        saved = deepcopy(history[index - 1])
        restored = deepcopy(history[-1])
        actual = {"bridge_pid": driver._session_bridge_pid, "episode_character_id": driver._episode_character_id,
            "episode_run_id": driver._episode_run_id, "campaign_goal": deepcopy(driver._campaign_goal),
            "succession_lifecycle": deepcopy(driver._succession_lifecycle), "pipe_name": driver.pipe_name}
    diagnostics, played = snapshot.get("diagnostics", {}), snapshot.get("played_character", {})
    if (diagnostics.get("bridge_pid") != actual["bridge_pid"]
            or played.get("character_id") != actual["episode_character_id"] or played.get("alive") is not True
            or snapshot.get("date_raw") != checkpoint.get("date_raw")
            or checkpoint.get("episode_character_id") != actual["episode_character_id"]
            or checkpoint.get("episode_run_id") != actual["episode_run_id"]
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("active_event") is not None or snapshot.get("pending_character_interaction") is not None):
        raise ValueError("native cold checkpoint differs from its original paused native frame")
    game = _process_identity(actual["bridge_pid"])
    if (not isinstance(game, Mapping) or game.get("pid") != actual["bridge_pid"]
            or not game.get("creation_date") or not game.get("executable")):
        raise ValueError("native cold projection lacks its actual Game birth/image")
    game = {"pid": game["pid"], "creation_date": game["creation_date"],
            "executable": os.path.normcase(os.path.abspath(game["executable"]))}
    native_frame = {key: deepcopy(snapshot.get(key)) for key in journal.FRAME[2:]}
    native_frame.update({key: diagnostics.get(key) for key in journal.FRAME[:2]})
    body = {"game_identity": game,
        "checkpoint": checkpoint, "saved_anchor": saved, "restore_row": restored,
        "native_frame": native_frame, "driver_binding": actual,
        "campaign_goal": normalize_ordinary_campaign_goal_v1(actual["campaign_goal"])}
    return NativeColdCheckpointProjectionV1(driver, _json(body), _SEAL)


def observe_native_cold_checkpoint_v1(owner, *, snapshot, expected_executable):
    """Bind the canonical App to its driver's retained internal cold projection.

    Normal queries may have followed the initial cold frame. No history scan,
    replay or extra native read is required to retain its exact provenance.
    """
    from .bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner
    driver = owner.driver
    projection = getattr(driver, "_successor_ui_cold_checkpoint_projection_v1", None)
    if (not isinstance(owner, SuccessorUIAppOwner) or owner.service.driver is not driver
            or getattr(owner.service, "_successor_ui_app_owner_v1", None) is not owner
            or not isinstance(projection, NativeColdCheckpointProjectionV1)
            or projection.seal is not _SEAL or projection.driver is not driver):
        raise TypeError("cold checkpoint lineage requires the canonical App's internal native projection")
    body = json.loads(projection.body)
    with driver._driver_state_lock:
        if (driver._driver_state_restored is not True or driver._driver_state_restore_kind != "cold_checkpoint"
                or driver._driver_state_error is not None or driver._last_checkpoint != body["checkpoint"]):
            raise ValueError("native driver's retained cold checkpoint is no longer current")
    game = journal.observe_game_identity_v1(snapshot, expected_executable)
    if game != body["game_identity"]:
        raise ValueError("retained native cold projection belongs to another Game birth")
    body.update(machine_id=owner.machine, source_epoch=owner.epoch)
    return NativeColdCheckpointLineageV1(owner, _json(body), projection, _SEAL)


def plan_resolved_checkpoint_retirement_v1(owner, *, anchor, cold):
    """Validate a narrow resolved archive plan; leave the original files intact.

    The anchor must be the saved completion producer's small local sidecar.
    Its JSON alone cannot issue the required canonical native cold token.
    """
    if (not isinstance(cold, NativeColdCheckpointLineageV1) or cold.seal is not _SEAL or cold.owner is not owner):
        raise TypeError("retirement requires this App's internally observed native cold lineage")
    observed = json.loads(cold.body)
    driver = owner.driver
    with driver._driver_state_lock:
        if (driver._driver_state_restore_kind != "cold_checkpoint" or driver._driver_state_restored is not True
                or driver._driver_state_error is not None
                or driver._last_checkpoint != observed["checkpoint"]
                or getattr(driver, "_successor_ui_cold_checkpoint_projection_v1", None) is not cold.projection
                or driver._session_bridge_pid != observed["game_identity"]["pid"]
                or driver._episode_character_id != observed["driver_binding"]["episode_character_id"]
                or driver._episode_run_id != observed["driver_binding"]["episode_run_id"]
                or normalize_ordinary_campaign_goal_v1(driver._campaign_goal) != observed["campaign_goal"]):
            raise ValueError("native cold lineage changed before its completed retirement plan")
    if (anchor.get("schema") != SCHEMA or anchor.get("action_replay_authorized") is not False
            or anchor.get("machine_id") != owner.machine or observed["machine_id"] != owner.machine
            or observed["source_epoch"] != owner.epoch
            or not _same_checkpoint(anchor.get("checkpoint"), observed["checkpoint"])
            or anchor.get("checkpoint") != observed["saved_anchor"]["result"].get("checkpoint")
            or normalize_ordinary_campaign_goal_v1(anchor.get("campaign_goal")) != observed["campaign_goal"]
            or anchor["driver_state_replace_receipt"]["attempt_binding"]["pipe_name"]
                != observed["driver_binding"]["pipe_name"]):
        raise ValueError("completed anchor differs from the actual restored SAVE/driver pair")
    old = anchor["game_identity"]
    new = observed["game_identity"]
    if (observed["restore_row"]["result"]["lifecycle"].get("previous_pid") != old.get("pid")
            or observed["restore_row"]["result"]["lifecycle"].get("pid") != new.get("pid")
            or old.get("creation_date") == new.get("creation_date")):
        raise ValueError("completed retirement has no actual replacement Game birth lineage")
    old_exit = _observe_old_game_exit_v1(old)
    ledger = journal.SuccessorUIPendingLedger(owner.root, machine_id=owner.machine,
        source_epoch=anchor["source_epoch"], game_identity=old,
        verify_transition=owner.validators._verify_natural_succession_transition,
        close_validator=owner.validators._ordinary_succession_close_issue,
        timeline_classifier=owner.validators._ordinary_succession_timeline_state)
    value, pin, intent_pin = _completion(ledger)
    if (pin != anchor.get("ledger_sha256") or intent_pin != anchor.get("close_intent_sha256")
            or value["transition_sha256"] != anchor.get("transition_sha256")
            or normalize_ordinary_campaign_goal_v1(value["campaign_goal"]) != observed["campaign_goal"]):
        raise ValueError("completed successor original evidence changed after its paired SAVE")
    # Recheck the exact small observation captured at the original SAVE. Do not
    # reconstruct a purported native snapshot from a summary or result fields.
    result = {"step": "save-checkpoint", "accepted": True, "checkpoint": anchor["checkpoint"],
        "materialization": {"available": True}, "driver_state_replace_receipt": anchor["driver_state_replace_receipt"]}
    if capture_completed_checkpoint_v1(ledger, save_result=result, snapshot=anchor["save_observation"]) != anchor:
        raise ValueError("completed checkpoint anchor differs from its original capture")
    evidence = {"schema": "xar.ck3.successor-ui-resolved-retirement-plan/v1",
        "original_ledger_sha256": pin, "original_close_intent_sha256": intent_pin,
        "checkpoint": observed["checkpoint"], "old_game_identity": old, "new_game_identity": new,
        "old_game_exit_observation": old_exit,
        "old_source_epoch": anchor["source_epoch"], "new_source_epoch": owner.epoch,
        "campaign_goal": observed["campaign_goal"], "action_replay_authorized": False,
        "canonical_ledger_changed": False}
    return ResolvedCheckpointRetirementV1(owner, ledger.path, pin,
        "successor-ui-resolved-" + pin + ".json", _json(evidence), _SEAL)


def write_completed_checkpoint_v1(owner, *, ledger, save_result, snapshot):
    """Persist the completed proof only after the original SAVE actually returns."""
    body = capture_completed_checkpoint_v1(ledger, save_result=save_result, snapshot=snapshot)
    path = owner.root / COMPLETION_FILE
    journal.write_json_atomic(path, body)
    with path.open("r+b") as stream:
        os.fsync(stream.fileno())
    actual, pin = journal._read(path)
    if actual != body:
        raise ValueError("completed checkpoint sidecar write/readback differs")
    return {"status": "captured", "path": str(path), "sha256": pin,
        "extra_history_free_observations": 1, "action_replay_authorized": False,
        "durability_scope": "FILE_FSYNC_READBACK_NOT_DIRECTORY_FSYNC"}


def retire_completed_checkpoint_v1(owner, plan):
    """Archive exact completed bytes, then move the canonical resolved ledger.

    Called under the App lock. There is no JSON authorization entry and no
    pending-state operation. A failure before the move leaves the old ledger;
    after-move readback failure restores its exact bytes when possible and is
    retained on the owner so a missing file cannot silently authorize Continue.
    """
    if (not isinstance(plan, ResolvedCheckpointRetirementV1) or plan.owner is not owner or plan.seal is not _SEAL
            or plan.ledger_path != owner.root / journal.FILE):
        raise TypeError("completed retirement requires this actual App's typed archive plan")
    raw = plan.ledger_path.read_bytes()
    if len(raw) > journal.LIMIT or hashlib.sha256(raw).hexdigest() != plan.ledger_sha256:
        raise ValueError("resolved ledger changed before its exact archive")
    folder = owner.root / "successor-ui-resolved-history"
    folder.mkdir(exist_ok=True)
    archive = folder / plan.archive_name
    if not archive.exists():
        with archive.open("xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    if archive.read_bytes() != raw:
        raise ValueError("completed successor archive differs from its exact original bytes")
    # This states the intended move, not a fabricated completed retirement.
    journal.write_json_atomic(folder / (plan.ledger_sha256 + ".retirement-intent.json"), {
        "status": "prepared", "archive": str(archive), "original_ledger_sha256": plan.ledger_sha256,
        "binding": json.loads(plan.evidence), "action_replay_authorized": False})
    if plan.ledger_path.read_bytes() != raw:
        raise ValueError("resolved ledger changed after its archive readback")
    os.replace(plan.ledger_path, archive)
    try:
        if archive.read_bytes() != raw:
            raise ValueError("retired successor archive failed its exact move readback")
    except Exception as error:
        owner._completed_retirement_error_v1 = str(error)
        if not plan.ledger_path.exists():
            with plan.ledger_path.open("xb") as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        raise
    return {"status": "retired_resolved", "archive": str(archive), "sha256": plan.ledger_sha256,
        "source_binding": json.loads(plan.evidence), "action_replay_authorized": False}
