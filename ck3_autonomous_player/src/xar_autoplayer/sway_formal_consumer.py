"""One-target, default-off Sway action and durable recovery policy.

The native submit ACK is deliberately pending-only.  A fresh native read,
independent of the receipt, proves an active matching scheme before resolution.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from pathlib import Path

from .bridge.driver import BridgeUnavailableError
from .environment import write_json_atomic


LEDGER_FILE = "active-scheme-sway-formal-private-v1.json"
SCHEMA = "xar.ck3.active-scheme-sway-formal-private.v1"


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def read_sway_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / LEDGER_FILE
    if not path.exists():
        return {"schema": SCHEMA, "pending": None, "resolved": None}
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or set(value) != {"schema", "pending", "resolved"}
            or value.get("schema") != SCHEMA
            or any(value[key] is not None and not isinstance(value[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("private Sway ledger is malformed")
    return value


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / LEDGER_FILE, dict(ledger))


def _identity(snapshot: Mapping[str, object], target: int) -> tuple[int, int, int, int]:
    played = snapshot.get("played_character")
    if isinstance(played, Mapping):
        actor_id = played.get("character_id")
        alive = played.get("alive")
        if (("played_character_id" in snapshot
             and snapshot["played_character_id"] != actor_id)
                or ("played_character_alive" in snapshot
                    and snapshot["played_character_alive"] is not alive)):
            raise ValueError("private Sway player identity differs across frame views")
    elif played is None:
        # _wait_for_readiness returns the verified compact binding, while
        # driver.take_snapshot() returns the full played_character object.
        actor_id = snapshot.get("played_character_id")
        alive = snapshot.get("played_character_alive")
    else:
        raise ValueError("private Sway played character is malformed")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or alive is not True or not _positive(actor_id)
            or not _positive(snapshot.get("revision"))
            or not _positive(snapshot.get("native_revision"))
            or type(snapshot.get("date_raw")) is not int
            or not _positive(target) or target > 0xFFFFFFFF
            or actor_id == target):
        raise ValueError("private Sway requires a living player and paused map frame")
    return (actor_id, snapshot["revision"],
            snapshot["native_revision"], snapshot["date_raw"])


def _read_matches(snapshot: Mapping[str, object], read: Mapping[str, object],
                  target: int) -> bool:
    actor, revision, native, date = _identity(snapshot, target)
    return bool(
        read.get("schema") == "active-scheme-sway-private-read-v1"
        and read.get("queried_revision") == revision
        and read.get("queried_native_revision") == native
        and read.get("snapshot_revision") == native
        and read.get("date_raw") == date
        and read.get("actor_character_id") == actor
        and read.get("target_character_id") == target
        and _positive(read.get("capture_epoch"))
        and _positive(read.get("container_generation"))
        and type(read.get("target_opinion_of_actor")) is int
        and -100 <= read["target_opinion_of_actor"] <= 100
        and type(read.get("active_scheme_count")) is int
        and 0 <= read["active_scheme_count"] <= 32
        and type(read.get("matching_sway_active")) is bool
        and type(read.get("native_legal_now")) is bool
    )


def should_submit_sway(snapshot: Mapping[str, object], read: Mapping[str, object],
                        target: int) -> bool:
    """Use an empty scheme slot for a low-opinion, explicitly selected relation.

    Fifty is the stock ordinary-AI start ceiling, not a continuation limit.
    """
    if not _read_matches(snapshot, read, target):
        raise ValueError("private Sway source differs from current paused frame")
    context = snapshot.get("active_context")
    if context is not None and not isinstance(context, Mapping):
        return False
    if isinstance(context, Mapping):
        if (context.get("active_event") is not None
                or context.get("pending_character_interaction") is not None):
            return False
    elif ("active_event" not in snapshot
          or "pending_character_interaction" not in snapshot):
        return False
    if (snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return False
    return bool(
        read["target_opinion_of_actor"] <= 50
        and read["active_scheme_count"] == 0
        and read["matching_sway_active"] is False
        and read["native_complete_can_send"] is True
        and read["native_legal_now"] is True
    )


def _read_now(driver: object, target: int) -> tuple[dict[str, object], dict[str, object]]:
    snapshot = driver.take_snapshot()
    _identity(snapshot, target)
    read = driver.query_active_scheme_sway_target_private_v1(
        expected_revision=snapshot["revision"], target_character_id=target)
    if not _read_matches(snapshot, read, target):
        raise BridgeUnavailableError("private Sway recovery read changed frame")
    return snapshot, read


def _resolved(ledger: Mapping[str, object], pending: Mapping[str, object],
              read: Mapping[str, object], receipt: Mapping[str, object] | None,
              state_dir: Path) -> dict[str, object]:
    if (read["matching_sway_active"] is not True
            or read["active_scheme_count"] < 1
            or (receipt is not None
                and read["capture_epoch"] <= pending["pre_capture_epoch"])):
        raise BridgeUnavailableError("private Sway has no independent active-scheme postcondition")
    result = {
        "status": "applied", "postcondition_verified": True,
        "actor_character_id": pending["actor_character_id"],
        "target_character_id": pending["target_character_id"],
        "action_id": pending["action_id"],
        "pre_capture_epoch": pending["pre_capture_epoch"],
        "post_capture_epoch": read["capture_epoch"],
        "post_native_revision": read["queried_native_revision"],
        "post_date_raw": read["date_raw"],
        "native_receipt": dict(receipt) if receipt is not None else None,
        "next_turn_consumed": False,
    }
    previous = ledger["resolved"]
    if isinstance(previous, Mapping):
        history = list(previous.get("previous_interventions", []))
        history.append({key: value for key, value in previous.items()
                        if key != "previous_interventions"})
        result["previous_interventions"] = history
    if isinstance(pending.get("followup"), Mapping):
        result["followup"] = dict(pending["followup"])
    _write(state_dir, {**ledger, "pending": None, "resolved": result})
    return result


def _same_target_followup(resolved: Mapping[str, object],
                          readback: Mapping[str, object]) -> dict[str, object]:
    """Use the retained end and current named benefit for a new episode only."""
    followup = {"previous_action_id": resolved["action_id"]}
    if readback["matching_sway_active"] is True:
        return {**followup, "decision": "retain_existing_sway"}
    terminal = resolved.get("terminal_intervention")
    if (not isinstance(terminal, Mapping)
            or terminal.get("instance_terminal_outcome_observed") is not True):
        return {**followup, "decision": "observe_tracked_instance_end"}
    followup.update({
        "scheme_instance_id": terminal["scheme_instance_id"],
        "scheme_instance_generation": terminal["scheme_instance_generation"],
        "terminal_cause_observed": terminal["terminal_cause_observed"],
        "terminal_cause": terminal["terminal_cause"],
    })
    if readback["active_scheme_count"] != 0:
        return {**followup, "decision": "defer_occupied_scheme_slot"}
    if readback["target_opinion_of_actor"] > 50:
        return {**followup, "decision": "finish_selected_relation"}
    material = resolved.get("material_intervention")
    if (not isinstance(material, Mapping)
            or material.get("dedicated_benefit_observed") is not True
            or material.get("source_date_raw") != readback["date_raw"]):
        return {**followup, "decision": "observe_current_named_relation_material"}
    return {**followup, "decision": "repeat_selected_target"}


def consume_sway_private_once(driver: object, *, target_character_id: int,
                              snapshot: Mapping[str, object],
                              readback: Mapping[str, object]) -> dict[str, object]:
    """Submit at most once; on a new PID use a read-only recovery first."""
    if getattr(driver, "allow_private_active_scheme_sway_action", False) is not True:
        raise ValueError("private Sway formal trial is disabled")
    state_dir = driver.state_dir
    if not isinstance(state_dir, Path):
        raise ValueError("private Sway requires managed state_dir")
    actor, _, _, _ = _identity(snapshot, target_character_id)
    if not _read_matches(snapshot, readback, target_character_id):
        raise ValueError("private Sway source differs from current paused frame")
    ledger = read_sway_ledger(state_dir)
    pending = ledger["pending"]
    if isinstance(pending, dict):
        if (pending.get("actor_character_id") != actor
                or pending.get("target_character_id") != target_character_id):
            return {"status": "pending_other_actor_or_target", "pending": pending}
        if readback["matching_sway_active"] is True:
            return _resolved(ledger, pending, readback, None, state_dir)
        return {"status": "pending_recovery", "pending": pending,
                "postcondition_verified": False}
    resolved = ledger["resolved"]
    followup = None
    if (isinstance(resolved, dict)
            and resolved.get("actor_character_id") == actor
            and resolved.get("target_character_id") == target_character_id):
        followup = _same_target_followup(resolved, readback)
        if followup["decision"] != "repeat_selected_target":
            return {"status": "already_applied", "resolved": resolved,
                    "followup": followup}
    elif isinstance(resolved, dict):
        followup = {"decision": "retarget_selected_relation",
                    "previous_action_id": resolved["action_id"]}
    if not should_submit_sway(snapshot, readback, target_character_id):
        return {"status": "no_positive_opportunity", "readback": dict(readback),
                **({"followup": {**followup, "decision": "native_start_unavailable"}}
                   if followup is not None else {})}

    action_id = "sway-" + uuid.uuid4().hex
    pending = {
        "stage": "submission_unresolved", "action_id": action_id,
        "actor_character_id": actor, "target_character_id": target_character_id,
        "pre_capture_epoch": readback["capture_epoch"],
        "pre_container_generation": readback["container_generation"],
        "pre_date_raw": readback["date_raw"],
        "pre_native_revision": readback["queried_native_revision"],
        "pre_target_opinion_of_actor": readback["target_opinion_of_actor"],
        **({"followup": followup} if followup is not None else {}),
    }
    # Durable intent precedes the native call.  If the call times out or the
    # process dies, a later run only reads game state and never resubmits.
    _write(state_dir, {**ledger, "pending": pending})
    try:
        ack = driver.submit_active_scheme_sway_private_v1(
            readback=dict(readback), action_id=action_id)
    except BridgeUnavailableError as error:
        return {"status": "submission_unresolved", "pending": pending,
                "submit_error": str(error), "postcondition_verified": False}
    pending = {**pending, "stage": "receipt_pending", "ack": ack}
    _write(state_dir, {**ledger, "pending": pending})
    try:
        receipt = driver.query_active_scheme_sway_receipt_private_v1(
            target_character_id=target_character_id, action_id=action_id,
            expected_revision=driver.take_snapshot()["native_revision"],
            pre_capture_epoch=readback["capture_epoch"])
    except BridgeUnavailableError as error:
        return {"status": "receipt_pending", "pending": pending,
                "receipt_error": str(error), "postcondition_verified": False}
    try:
        _, after_read = _read_now(driver, target_character_id)
        return _resolved(ledger, pending, after_read, receipt, state_dir)
    except BridgeUnavailableError as error:
        return {"status": "postcondition_pending", "pending": pending,
                "native_receipt": receipt, "postcondition_error": str(error),
                "postcondition_verified": False}


def consume_sway_following_turn(state_dir: Path,
                                snapshot: Mapping[str, object]) -> dict[str, object] | None:
    """Consume current and prior episode observations after the ordinary turn."""
    ledger = read_sway_ledger(state_dir)
    resolved = ledger["resolved"]
    if not isinstance(resolved, dict):
        return None
    current = _consume_episode_following_turn(resolved, snapshot)
    previous = resolved.get("previous_interventions", [])
    history = []
    history_changed = False
    for episode in previous:
        consumed = _consume_episode_following_turn(episode, snapshot)
        history.append(consumed if consumed is not None else episode)
        history_changed = history_changed or consumed is not None
    if current is None and not history_changed:
        return None
    resolved = dict(current if current is not None else resolved)
    if previous:
        resolved["previous_interventions"] = history
    _write(state_dir, {**ledger, "resolved": resolved})
    return resolved


def _consume_episode_following_turn(resolved: Mapping[str, object],
                                    snapshot: Mapping[str, object]):
    from .sway_material_consumer import consume_sway_material_following_turn

    try:
        actor_id, _, _, _ = _identity(
            snapshot, resolved.get("target_character_id"))
    except ValueError:
        return None
    if actor_id != resolved.get("actor_character_id"):
        return None
    material = consume_sway_material_following_turn(
        resolved.get("material_intervention"), actor_character_id=actor_id,
        native_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"],
    )
    terminal = consume_sway_material_following_turn(
        resolved.get("terminal_intervention"), actor_character_id=actor_id,
        native_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"],
    )
    stop_record = resolved.get("stop_intervention")
    stop = (consume_sway_material_following_turn(
        stop_record, actor_character_id=actor_id,
        native_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"],
    ) if isinstance(stop_record, Mapping)
         and stop_record.get("postcondition_verified") is True else None)
    start_consumed = (resolved.get("next_turn_consumed") is not True
                      and (snapshot["native_revision"] > resolved["post_native_revision"]
                           or snapshot["date_raw"] > resolved["post_date_raw"]))
    if not start_consumed and material is None and terminal is None and stop is None:
        return None
    if start_consumed:
        resolved = {**resolved, "next_turn_consumed": True,
                    "following_native_revision": snapshot["native_revision"],
                    "following_date_raw": snapshot["date_raw"]}
    if material is not None:
        resolved = {**resolved, "material_intervention": material}
    if terminal is not None:
        resolved = {**resolved, "terminal_intervention": terminal}
    if stop is not None:
        resolved = {**resolved, "stop_intervention": stop}
    return resolved
