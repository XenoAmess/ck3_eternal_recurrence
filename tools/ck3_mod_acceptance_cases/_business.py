"""Shared evidence handling; no host, source, DLL, launch, or lease selection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def require(value, reason):
    if not value:
        raise ValueError(reason)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check_evidence(row):
    require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "Exact evidence pin required")
    actual = pin(row["path"])
    require(actual["bytes"] == row["bytes"] and actual["sha256"] == row["sha256"], "Evidence changed")
    return actual


def case_config(context):
    location = context["case_spec"]["adapter"]["config"]
    path = Path(location)
    if not path.is_absolute():
        path = Path(context["repo_root"]) / path
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def review(client, name, requirements, details=None):
    response = client.root_checkpoint(name, {
        "schema": "ck3-product-root-business-checkpoint-v1",
        "requirements": requirements,
        "details": details or {},
        "business_pass_inferred": False,
    })
    require(response.get("status") == "complete", "Root business checkpoint remains pending: " + name)
    require(isinstance(response.get("facts"), dict) and
            all(response["facts"].get(key) is True for key in requirements),
            "Actual original business facts missing: " + name)
    require(isinstance(response.get("evidence"), list) and response["evidence"],
            "Root review needs frozen actual evidence")
    for row in response["evidence"]:
        check_evidence(row)
    client.checkpoint(name + "-accepted", response)
    return response


def observe(client, name, allow_actor_change=False):
    # No post-ACK active_event:null expectation: an unknown next event is observed.
    row = client.execute_plan([{
        "id": name, "tool": "ck3_take_snapshot",
        "args": {"include_native_command_history": False}, "fresh_revision": True,
    }], name)[0]
    frame = row["result"]
    event_number = 0
    while frame.get("active_event") is not None:
        event_number += 1
        context_name = name + "-event-" + str(event_number).zfill(3)
        context_rows = client.execute_plan([{
            "id": context_name, "tool": "ck3_query_current_event_window_context_v1",
            "args": {}, "fresh_revision": True,
        }], context_name)
        review(client, context_name + "-review", ["exact_current_event_source_identified", "selected_enabled_option_once"], {
            "actual_event": frame["active_event"], "actual_context": context_rows[0],
            "after_rule": "Observe current owner/date/paused/map and the next event. Never assert no next event, repeat an ACK, or guess ROOT/definition IDs.",
        })
        next_name = context_name + "-after"
        row = client.execute_plan([{"id": next_name, "tool": "ck3_take_snapshot",
                                    "args": {"include_native_command_history": False}, "fresh_revision": True}], next_name)[0]
        next_frame = row["result"]
        require(next_frame.get("active_event") != frame.get("active_event"), "Reviewed event was not consumed; do not replay")
        frame = next_frame
    return client.validate_frame(frame, allow_actor_change), row


def original_day(client, name, initial_date, limit=None, allow_actor_change=False):
    row = client.execute_plan([{"id": name, "kind": "advance_day", "days": 1, "timeout": 300}], name, 300)[0]
    value = row["result"]
    before, after = value.get("before"), value.get("after")
    require(isinstance(before, dict) and isinstance(after, dict), "Actual day boundary snapshots missing")
    elapsed = after.get("date_raw", 0) - before.get("date_raw", 0)
    require(type(elapsed) is int and 0 < elapsed < 48, "Original day boundary was not bounded")
    if value.get("requested_days") != 1 or value.get("requested_interval_complete") is not True or value.get("event_boundary") is not None:
        # Natural notifications are a real boundary; date/native alone never grant day credit.
        review(client, name + "-boundary", ["original_submitted_day_semantically_proven"], {
            "actual_day_row": row, "never_replay_this_day": True,
            "reason": "Review the actual original boundary and event source; elapsed date alone is insufficient.",
        })
    frame, _ = observe(client, name + "-settled", allow_actor_change)
    if limit is not None:
        require(frame["date_raw"] - initial_date <= limit * 24, "Original natural day cap exceeded")
    return row, frame


def literals(client, name, required, forbidden):
    rows = client.execute_plan([{"id": name, "tool": "ck3_query_engine_log_literals_v1",
                                 "args": {"literals": list(required) + list(forbidden)}, "fresh_revision": True}], name)
    result = rows[0]["result"]
    require(result.get("read_only") is True and result.get("exists") is True and result.get("case_sensitive") is True,
            "Actual case-sensitive engine log unavailable")
    matches = result.get("matches", [])
    for literal, expected in [(item, 1) for item in required] + [(item, 0) for item in forbidden]:
        found = [item for item in matches if item.get("literal") == literal]
        require(len(found) == 1 and found[0].get("line_count") == expected,
                "Original exact marker gate rejected: " + literal)
    return rows[0]


def root_response_inputs(context):
    return context.get("case_inputs", {})


def final_root_evidence(context, required_names):
    output = Path(context["output"])
    proofs = []
    for name in required_names:
        path = output / (name + "-accepted.json")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        require(value.get("reviewer") == "/root" and value.get("run_id") == context["run_id"] and value.get("status") == "complete",
                "Actual Root review crossed scene")
        for evidence in value["evidence"]:
            check_evidence(evidence)
        proofs.append(pin(path))
    return proofs
