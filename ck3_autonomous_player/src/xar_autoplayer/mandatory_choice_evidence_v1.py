"""Immutable evidence for an explicitly proved native blocking choice.

The live planner only writes a before/after pair. Source review consumes
completed pairs in a separate process; it never gates the next game turn.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import uuid


SCHEMA = "xar.unknown-mandatory-choice-incident/v1"
DIRECTORY = "unknown-mandatory-choices"


def _write_once(path: Path, value: dict) -> dict:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists():
        temporary.unlink()
        raise FileExistsError(str(path))
    os.replace(temporary, path)
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def capture_before(state_dir: str | Path, planned: dict) -> dict:
    """Freeze the full native catalogue and source frame before token dispatch."""
    plan = planned.get("plan") if isinstance(planned, dict) else None
    capture = plan.get("unknown_mandatory_choice_v1") if isinstance(plan, dict) else None
    if not isinstance(capture, dict) or capture.get("schema") != SCHEMA:
        raise ValueError("missing mandatory-choice capture")
    frame = capture.get("frame_binding")
    selection = capture.get("selection")
    dto = capture.get("native_window")
    proof = dto.get("blocking_proof") if isinstance(dto, dict) else None
    choices = dto.get("choices") if isinstance(dto, dict) else None
    selected_rows = (
        [row for row in choices if isinstance(row, dict)
         and row.get("choice_id") == selection.get("choice_id")]
        if isinstance(choices, list) and isinstance(selection, dict) else []
    )
    if (not isinstance(frame, dict) or not isinstance(selection, dict)
            or not isinstance(dto, dict)
            or dto.get("schema") != "xar.native-mandatory-choice-window/v1"
            or dto.get("frame_binding") != frame
            or not isinstance(proof, dict)
            or proof.get("kind") not in {"blocks_simulation", "exclusive_modal_blocks_input"}
            or proof.get("verified") is not True
            or not isinstance(proof.get("source"), str) or not proof["source"]
            or dto.get("choices_complete") is not True
            or len(selected_rows) != 1
            or selected_rows[0].get("action_token") != selection.get("action_token")
            or selected_rows[0].get("visible") is not True
            or selected_rows[0].get("enabled") is not True
            or selected_rows[0].get("is_choice") is not True
            or planned.get("snapshot_id") != frame.get("snapshot_id")
            or planned.get("revision") != frame.get("revision")
            or plan.get("selected_step") != selection.get("selected_step")
            or selection.get("action_token") is None
            or selection.get("choice_id") is None
            or capture.get("blocking_proof_verified") is not True
            or capture.get("catalogue_complete") is not True):
        raise ValueError("mandatory-choice capture lost frame, proof or selection")
    directory = Path(state_dir) / "evidence" / DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    incident = uuid.uuid4().hex
    before = {**copy.deepcopy(capture), "incident_id": incident,
              "stage": "before_submission", "captured_at_utc": _utc(),
              "dispatch_attempted": False, "offline_followup_required": True,
              "replay_allowed": False}
    receipt = _write_once(directory / (incident + ".before.json"), before)
    return {"incident_id": incident, "before": receipt, "directory": str(directory),
            "window_id": dto.get("window_id"), "instance": dto.get("window_instance_id"),
            "choice_id": selection["choice_id"], "action_token": selection["action_token"]}


def capture_after(ticket: dict, *, outcome: dict | None = None,
                  error: BaseException | None = None) -> dict:
    """Record the original ACK and later postcondition without replay or credit."""
    result = outcome.get("result") if isinstance(outcome, dict) else None
    post = result.get("mandatory_choice_postcondition") if isinstance(result, dict) else None
    verified = bool(
        isinstance(result, dict) and result.get("accepted") is True
        and isinstance(post, dict)
        and post.get("verified") is True
        and post.get("old_window_id") == ticket["window_id"]
        and post.get("old_instance") == ticket["instance"]
        and post.get("selected_choice_id") == ticket["choice_id"]
        and post.get("old_window_no_longer_blocking") is True
    )
    after = {"schema": SCHEMA, "incident_id": ticket["incident_id"],
             "stage": "after_response", "captured_at_utc": _utc(),
             "before": ticket["before"],
             "command_acknowledged": isinstance(result, dict) and result.get("accepted") is True,
             "original_blocking_window_advanced_verified": verified,
             "action_receipt": copy.deepcopy(result),
              "error": ({"type": type(error).__name__, "message": str(error),
                         "native_raw_receipt": copy.deepcopy(getattr(
                             error, "mandatory_choice_raw_receipt", None))}
                        if error else None),
             "replay_allowed": False, "material_effects_verified": False,
             "offline_followup_required": True}
    receipt = _write_once(Path(ticket["directory"]) / (ticket["incident_id"] + ".after.json"), after)
    return {"incident_id": ticket["incident_id"], "before": ticket["before"],
            "after": receipt, "original_blocking_window_advanced_verified": verified,
            "replay_allowed": False, "material_effects_verified": False}


def collect_completed(state_dir: str | Path, seen_incident_ids=()) -> list[dict]:
    """Read only immutable completed pairs for asynchronous source review."""
    directory = Path(state_dir) / "evidence" / DIRECTORY
    seen = set(seen_incident_ids)
    rows = []
    for before_path in sorted(directory.glob("*.before.json")):
        incident = before_path.name.removesuffix(".before.json")
        after_path = before_path.with_name(incident + ".after.json")
        if incident in seen or not after_path.is_file():
            continue
        before_raw, after_raw = before_path.read_bytes(), after_path.read_bytes()
        before, after = json.loads(before_raw), json.loads(after_raw)
        if (before.get("schema") != SCHEMA or after.get("schema") != SCHEMA
                or before.get("incident_id") != incident
                or after.get("incident_id") != incident
                or after.get("before", {}).get("sha256") != hashlib.sha256(before_raw).hexdigest()):
            raise ValueError("mandatory-choice incident pair identity changed")
        rows.append({"incident_id": incident, "kind": "unknown_mandatory_choice",
                     "window_id": before["native_window"].get("window_id"),
                     "instance": before["native_window"].get("window_instance_id"),
                     "selection": before["selection"],
                     "original_blocking_window_advanced_verified": after[
                         "original_blocking_window_advanced_verified"],
                     "before": str(before_path), "before_sha256": hashlib.sha256(before_raw).hexdigest(),
                     "after": str(after_path), "after_sha256": hashlib.sha256(after_raw).hexdigest()})
    return rows
