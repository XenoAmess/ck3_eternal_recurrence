"""Game-date stability window. Local evidence accounting only; never an MCP caller."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid

SCHEMA = "root.ck3.continuity-window/v1"
TARGET_DAYS = 10958  # ceil(30 * 365.25); raw CK3 dates are hours.
TARGET_RAW = TARGET_DAYS * 24
MAX_RECEIPT_BYTES = 65536


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("invalid " + name)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def frame_binding(frame):
    if not isinstance(frame, dict):
        raise ValueError("settled frame must be an object")
    return {"date_raw": integer(frame.get("date_raw"), "settled date"),
        "actor_character_id": integer(frame.get("actor_character_id"), "actor", 1),
        "episode_run_id": str(frame.get("episode_run_id") or ""),
        "snapshot_id": frame.get("snapshot_id"), "revision": frame.get("revision"),
        "native_revision": frame.get("native_revision")}


def game_binding(value):
    pid = integer(value.get("pid"), "Game PID", 1)
    birth = value.get("creation_date")
    if not isinstance(birth, str) or not birth:
        raise ValueError("actual Game creation identity required")
    return {"pid": pid, "creation_date": birth}


def transition(previous, kind, details):
    """Pure reducer. Only repair completion can open/reset a stability window."""
    if not isinstance(details, dict) or not details.get("evidence_id") or not details.get("source"):
        raise ValueError("exact source and evidence ID required")
    state = deepcopy(previous)
    if state is None:
        if kind != "repair_required":
            raise ValueError("initialize from the real blocking failure, not old campaign age")
        state = {"schema": SCHEMA, "machine_id": details["machine_id"], "window_id": 0,
            "status": "prepared", "start_date_raw": None, "target_date_raw": None,
            "target_days": TARGET_DAYS, "target_years": 30, "calendar_year_days": 365.25,
            "manual_repair_count": 0, "automatic_recovery_count": 0,
            "binding_lineage_count": 0, "latest_binding": None,
            "game_binding": game_binding(details["game"]), "sequence": 0}
    if state.get("schema") != SCHEMA or state.get("target_days") != TARGET_DAYS:
        raise ValueError("different continuity policy/schema")
    if details.get("machine_id", state["machine_id"]) != state["machine_id"]:
        raise ValueError("continuity machine identity changed")
    if "game" in details and game_binding(details["game"]) != state["game_binding"]:
        raise ValueError("same-campaign Game generation changed; explicit handoff required")
    if kind == "repair_required":
        frame = frame_binding(details["frame"])
        cycles = integer(details["completed_cycles"], "settled cycles")
        state.update(status="prepared" if state["window_id"] == 0 else "repair_required", interrupted_window_id=state["window_id"],
            interruption={"reason": details["reason"], "source": details["source"],
                "evidence_id": details["evidence_id"], "last_settled_frame": frame,
                "completed_cycles": cycles},
            last_settled_date_raw=frame["date_raw"], last_settled_cycles=cycles)
    elif kind == "attach_verified":
        frame = frame_binding(details["frame"])
        cycles = integer(details["completed_cycles"], "settled cycles")
        if not frame["episode_run_id"]:
            raise ValueError("actual episode binding required")
        if state["status"] in ("prepared", "repair_required"):
            state.update(window_id=state["window_id"] + 1, status="running",
                start_date_raw=frame["date_raw"], target_date_raw=frame["date_raw"] + TARGET_RAW,
                manual_repair_count=state["manual_repair_count"] + 1,
                window_start_source=details["source"], previous_interruption=state.get("interruption"))
        elif state["status"] not in ("running", "complete"):
            raise ValueError("unsupported continuity status")
        elif frame["date_raw"] < state["last_settled_date_raw"] or cycles < state["last_settled_cycles"]:
            raise ValueError("verified handoff moved backwards without a recorded repair")
        state.update(last_settled_date_raw=frame["date_raw"], last_settled_cycles=cycles)
        old_binding = state.get("latest_binding")
        if old_binding and any(frame[k] != old_binding[k] for k in ("actor_character_id", "episode_run_id")):
            state["binding_lineage_count"] += 1
        state["latest_binding"] = frame
    elif kind in ("settled_batch", "automatic_recovery"):
        if state["status"] not in ("running", "complete"):
            raise ValueError("manual repair remains unresolved")
        date = integer(details["date_raw"], "settled date")
        cycles = integer(details["completed_cycles"], "settled cycles")
        # A watchdog can reread an older, already settled original control.
        # Such observation grants no additional date/cycle credit.
        if date < state["last_settled_date_raw"] or cycles < state["last_settled_cycles"]:
            if date <= state["last_settled_date_raw"] and cycles <= state["last_settled_cycles"]:
                return state
            raise ValueError("inconsistent settled date/cycle chain")
        state.update(last_settled_date_raw=date, last_settled_cycles=cycles,
            last_settled_source=details["source"])
        if kind == "automatic_recovery":
            state["automatic_recovery_count"] += 1
        if isinstance(details.get("frame"), dict):
            frame = frame_binding(details["frame"])
            if frame["date_raw"] != date:
                raise ValueError("settled frame/date mismatch")
            old_binding = state.get("latest_binding")
            if old_binding and any(frame[k] != old_binding[k] for k in ("actor_character_id", "episode_run_id")):
                state["binding_lineage_count"] += 1
            state["latest_binding"] = frame
        if date >= state["target_date_raw"]:
            state["status"] = "complete"
    else:
        raise ValueError("unsupported continuity transition")
    return state


def summary(state):
    start = state.get("start_date_raw")
    elapsed = 0 if start is None else max(0, state["last_settled_date_raw"] - start)
    return {"window_id": state["window_id"], "status": state["status"],
        "start_date_raw": start, "last_settled_date_raw": state["last_settled_date_raw"],
        "last_settled_cycles": state["last_settled_cycles"], "target_date_raw": state["target_date_raw"],
        "elapsed_days": elapsed / 24, "target_days": TARGET_DAYS,
        "target_reached": state["status"] == "complete"}


def read_small(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("continuity receipt exceeds finite small bound")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("continuity receipt must be an object")
    return value


def pin(path, limit=1024**2):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError("named continuity evidence exceeds bound")
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


def _atomic(path, value, replace=False):
    payload = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("continuity output exceeds finite small bound")
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    with tmp.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if replace:
            os.replace(tmp, path)
        else:
            tmp.rename(path)
    finally:
        tmp.unlink(missing_ok=True)


class WindowLedger:
    """Small atomic snapshot plus immutable, recoverable ordered transition receipts."""
    def __init__(self, path):
        self.path = Path(path)
        self.events = self.path.with_name("ROOT-CONTINUITY-WINDOW-EVENTS")

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix(".lock").open("a+b") as stream:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _load(self):
        state = read_small(self.path) if self.path.exists() else None
        sequence = state["sequence"] if state else 0
        # Recover only committed exact next receipts, without enumerating histories.
        while (self.events / f"{sequence + 1:08d}.json").exists():
            event = read_small(self.events / f"{sequence + 1:08d}.json")
            if event["previous_sha256"] != digest(state) or event["after"]["sequence"] != sequence + 1:
                raise ValueError("continuity event chain differs")
            state = event["after"]
            _atomic(self.path, state, replace=True)
            sequence += 1
        if state and sequence:
            committed = read_small(self.events / f"{sequence:08d}.json")
            key = digest({"kind": committed["kind"], "evidence_id": committed["details"]["evidence_id"]})
            index = self.events / ("source-" + key + ".json")
            if not index.exists():
                _atomic(index, {"sequence": sequence, "identity": committed["identity"]})
        return state

    def apply(self, kind, details):
        with self.locked():
            self.events.mkdir(exist_ok=True)
            previous = self._load()
            identity = digest({"kind": kind, "details": details})
            key = digest({"kind": kind, "evidence_id": details.get("evidence_id")})
            index = self.events / ("source-" + key + ".json")
            if index.exists():
                if read_small(index)["identity"] != identity:
                    raise ValueError("same continuity evidence ID changed contents")
                return previous
            after = transition(previous, kind, details)
            if after == previous:
                return previous
            sequence = (previous["sequence"] if previous else 0) + 1
            after.update(sequence=sequence, last_event_identity=identity)
            event = {"sequence": sequence, "at_utc": datetime.now(timezone.utc).isoformat(),
                "kind": kind, "details": details, "identity": identity,
                "previous_sha256": digest(previous), "after": after}
            _atomic(self.events / f"{sequence:08d}.json", event)
            _atomic(self.path, after, replace=True)
            _atomic(index, {"sequence": sequence, "identity": identity})
            return after

    def load(self):
        with self.locked():
            return self._load()


def initialize_repair(ledger, state_path, failure_response, launch_path, machine_id, reason):
    state = read_small(state_path)
    launch = read_small(launch_path)
    return WindowLedger(ledger).apply("repair_required", {
        "machine_id": machine_id, "game": game_binding(launch), "frame": state["before"],
        "completed_cycles": state["completed_cycles"], "reason": reason,
        "evidence_id": "manual-repair:" + str(Path(failure_response).resolve()),
        "source": {"settled_state": pin(state_path), "failure_response": pin(failure_response)}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("initialize-repair")
    for name in ("state", "failure-response", "launch"):
        init.add_argument("--" + name, type=Path, required=True)
    init.add_argument("--machine-id", required=True)
    init.add_argument("--reason", required=True)
    sub.add_parser("show")
    args = parser.parse_args()
    state = (initialize_repair(args.ledger, args.state, args.failure_response, args.launch, args.machine_id, args.reason)
        if args.command == "initialize-repair" else WindowLedger(args.ledger).load())
    print(json.dumps(summary(state), ensure_ascii=False, indent=2))
