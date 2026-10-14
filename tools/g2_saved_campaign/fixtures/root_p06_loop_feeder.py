"""Advance the one live Robert queue in ordered 30-turn batches until its goal or a halt.

This process never calls CK3 or MCP. It publishes a new local queue control only
after the preceding one has a successful, exact response. A halt requires review.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time


N = Path(__file__).resolve().parent
FIRST_CONTROL_SEQUENCE = 965
TARGET_DAYS = 30 * 365.25


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, value: dict) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def status(value: str, **details: object) -> None:
    atomic(N / "ROOT-CONTINUOUS-FEEDER-STATUS-P06.json", {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "status": value,
        "first_control_sequence": FIRST_CONTROL_SEQUENCE,
        "campaign_target_days": TARGET_DAYS,
        **details,
    })


def main() -> None:
    root = N / "p06-queue"
    if not (root / "ROOT-P06-CAMPAIGN-VERIFIED.json").is_file():
        raise RuntimeError("actual warm Game/SDK identity is not bound")
    seed = read(N / "ROOT-COLD-CUMULATIVE-SEED.json")
    start_date_raw = seed["start_date_raw"]
    if type(start_date_raw) is not int or seed["completed_cycles"] != 1085:
        raise ValueError("frozen campaign start/cycle source differs")
    incident_index = set()
    for old_batch in N.glob("*offline-batches/*.json"):
        for item in read(old_batch).get("new_incidents", []):
            if item.get("before"):
                incident_index.add(Path(item["before"]).name)
    current_control = FIRST_CONTROL_SEQUENCE
    status("following_actual_control", control_sequence=current_control)
    while True:
        if (N / "ROOT-CONTINUOUS-FEEDER-STOP-P06").exists():
            status("operator_stopped", control_sequence=current_control)
            return
        response = N / "p06-responses" / f"{current_control:04d}-1-result.json"
        if not response.is_file():
            if (N / "REQUEST-ADMISSION-CLOSED").exists() or (N / "EXIT-SDK").exists():
                status("sdk_admission_closed", control_sequence=current_control)
                return
            time.sleep(2)
            continue
        row = read(response)
        if row.get("request") != {
            "sequence": current_control, "command": "full_loop", "arguments": {"max_turns": 1 if current_control == FIRST_CONTROL_SEQUENCE else 30}
        }:
            raise ValueError("exact existing full_loop control response differs")
        wrapper = row.get("result")
        result = wrapper.get("structured_content") if isinstance(wrapper, dict) else None
        if (not isinstance(result, dict) or wrapper.get("is_error") is not False
                or result.get("status") != "bounded_loop_finished"
                or type(result.get("actual_end_date_raw")) is not int):
            status("halted_review_required", control_sequence=current_control,
                   response=str(response), halt=str(N / "ROOT-CURRENT-HALT-P06.json"))
            return
        incident_root = N / "state/evidence/unhandled-events"
        new_incidents = []
        for before in sorted(incident_root.glob("*.before.json")):
            if before.name in incident_index:
                continue
            evidence = read(before)
            after = before.with_name(before.name.replace(".before.json", ".after.json"))
            item = {"incident_id": evidence.get("incident_id"),
                    "event_definition_key": evidence.get("event_definition_key"),
                    "current_event_instance_id": evidence.get("current_event_instance_id"),
                    "binding": evidence.get("binding"), "selection": evidence.get("selection"),
                    "before": str(before), "before_sha256": hashlib.sha256(before.read_bytes()).hexdigest(),
                    "after": str(after) if after.exists() else None,
                    "after_sha256": hashlib.sha256(after.read_bytes()).hexdigest() if after.exists() else None}
            new_incidents.append(item)
            incident_index.add(before.name)
        batch_root = N / "p06-offline-batches"
        batch_root.mkdir(exist_ok=True)
        atomic(batch_root / f"{current_control:04d}.json", {
            "at_utc": datetime.now(timezone.utc).isoformat(),
            "completed_control_sequence": current_control, "control_response": str(response),
            "cumulative_cycles": result.get("cumulative_cycles"),
            "offline_analysis_pending": bool(new_incidents), "new_incidents": new_incidents,
            "instruction": "Analyze collected incidents offline and batch-fill shared registry/policy while the next batch continues."})
        date_raw = result["actual_end_date_raw"]
        days = (date_raw - start_date_raw) / 24
        if days >= TARGET_DAYS:
            status("thirty_year_date_reached_review_required", control_sequence=current_control,
                   response=str(response), date_raw=date_raw, elapsed_days=days,
                   completed_cycles=result.get("cumulative_cycles"))
            return
        if result.get("same_SDK_continuation_available") is not True:
            status("campaign_terminal_review_required", control_sequence=current_control,
                   response=str(response), date_raw=date_raw, elapsed_days=days,
                   reason=result.get("reason"))
            return
        sequence = result.get("next_sequence")
        next_receipt = read(N / "NEXT-SEQUENCE-P06.json")
        if (type(sequence) is not int or sequence <= current_control
                or next_receipt.get("next_sequence") != sequence):
            raise ValueError("the queue did not grant one exact next control sequence")
        inbox = N / "p06-requests" / f"{sequence:04d}-1-result.json"
        outbox = N / "p06-responses" / inbox.name
        request = {"sequence": sequence, "command": "full_loop", "arguments": {"max_turns": 30}}
        if inbox.exists():
            if read(inbox) != request:
                raise ValueError("next control path is occupied by a different request")
            if not outbox.exists():
                raise ValueError("next control already inflight; a second feeder must not publish")
        else:
            atomic(inbox, request)
        status("following_actual_control", control_sequence=sequence,
               prior_response=str(response), date_raw=date_raw, elapsed_days=days,
               completed_cycles=result.get("cumulative_cycles"))
        current_control = sequence


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        status("feeder_error_review_required", error_type=type(error).__name__, error=str(error)[:2048])
        raise
