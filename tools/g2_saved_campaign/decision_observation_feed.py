"""Publish actual SDK plans/results to a shared overlay feed across queue prefixes.

All paths come from the caller's admitted session. Import performs no I/O.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

MAX_OBSERVATION_BYTES = 16384


def _publish_new(path, value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_OBSERVATION_BYTES:
        raise ValueError("compact observation exceeds16KiB; original retained")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
        # No occupied-name overwrite on either Windows or POSIX.
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def relay_compact(source, compact, *, feed_root):
    """Namespace an already-written actual observation by its source directory."""
    source = Path(source).resolve()
    feed_root = Path(feed_root).resolve()
    if not source.is_file() or not isinstance(compact, dict):
        raise ValueError("relay requires the actual already-written source and compact object")
    if not (source.name.endswith("-0-plan.json") or source.name.endswith("-1-result.json")):
        raise ValueError("relay accepts actual plan/tool result observations only")
    if source.parent == feed_root:
        return source
    namespace = source.parent.name
    row = {**compact, "source_ref": str(source), "source_namespace": namespace}
    return _publish_new(feed_root / f"{namespace}-{source.name}", row)


def compact_plan(actual):
    """Small display projection; the full actual plan remains in its original receipt."""
    plan = {key: actual[key] for key in ("policy", "phase", "selected_step", "reason",
            "decision", "declaration", "prewar_force_admission") if key in actual}
    for key in ("reason", "selected_step", "policy", "phase"):
        if isinstance(plan.get(key), str):
            plan[key] = plan[key][:1200]
    admission = plan.get("prewar_force_admission")
    if isinstance(admission, dict):
        plan["prewar_force_admission"] = {key: admission[key] for key in (
            "status", "reason", "declare_admitted", "force_risk_qualified", "force_risk") if key in admission}
    return plan


def publish_before_submit(observation, *, current_request_path, game_launch_receipt,
                          response_root, feed_root, project_plan=compact_plan):
    """Publish one real Service callback using this queue's explicit context/output.

    Callers with an existing richer display projection can pass it as project_plan.
    Publication is a plan observation and never an execution or business outcome.
    """
    context = json.loads(Path(current_request_path).read_text(encoding="utf-8-sig"))
    launch = json.loads(Path(game_launch_receipt).read_text(encoding="utf-8-sig"))
    sequence = context.get("sequence")
    if type(sequence) is not int or sequence < 1 or context.get("tool") != "ck3_auto_turn":
        raise ValueError("pre-submit publication lacks this queue's held auto-turn request")
    actual = observation.get("plan")
    if not isinstance(actual, dict) or actual.get("selected_step") != observation.get("selected_step"):
        raise ValueError("actual selected plan is missing")
    plan = project_plan(actual)
    if not isinstance(plan, dict) or plan.get("selected_step") != actual.get("selected_step"):
        raise ValueError("display projection differs from the actual selected step")
    body = {"status": "planned", "plan": plan, "selected_step": observation["selected_step"],
            "snapshot_id": observation.get("snapshot_id"), "revision": observation.get("revision")}
    row = {"ended_at_utc": datetime.now(timezone.utc).isoformat(),
           "source": "actual GameplayBridgeService.before_submit callback",
           "game_pid": launch["pid"], "game_creation_date": launch["creation_date"],
           "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": sequence},
           "result": {"is_error": False, "structured_content": body}}
    output = _publish_new(Path(response_root).resolve() / f"{sequence:04d}-0-plan.json", row)
    relay_compact(output, row, feed_root=feed_root)


def error_projection(row):
    result = row.get("result")
    result = result if isinstance(result, dict) else {}
    messages = [str(row["client_error"])[:2048]] if row.get("client_error") else []
    messages += [block["text"][:2048] for block in result.get("content", [])[:3]
                 if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)]
    return {"request": row.get("request"), "ended_at_utc": row.get("ended_at_utc"),
            "source": "compact actual SDK error; original response retained",
            "result": {"is_error": True, "structured_content": {
                "status": "error", "message": "\n".join(messages)[:6144],
                "outcome_verified": False, "original_request_replayed": False}}}
