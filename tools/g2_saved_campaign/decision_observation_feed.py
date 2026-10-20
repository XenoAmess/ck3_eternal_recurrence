"""Publish bounded display projections; import performs no I/O."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

from decision_display_contract_v1 import Record, exact_int, maybe_record, project_plan, record

MAX_OBSERVATION_BYTES = 16384


def _publish_new(path: Path, value: Record) -> Path:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_OBSERVATION_BYTES:
        raise ValueError("compact observation exceeds16KiB; original retained")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def relay_compact(source: str | Path, compact: object, *, feed_root: str | Path) -> Path:
    """Namespace an actual, already-written plan/result using its source directory."""
    source = Path(source).resolve()
    target = Path(feed_root).resolve()
    actual = record(compact)
    if not source.is_file():
        raise ValueError("relay requires the actual already-written source")
    if not (source.name.endswith("-0-plan.json") or source.name.endswith("-1-result.json")):
        raise ValueError("relay accepts actual plan/tool result observations only")
    if source.parent == target:
        return source
    namespace = source.parent.name
    row = {**actual, "source_ref": str(source), "source_namespace": namespace}
    return _publish_new(target / f"{namespace}-{source.name}", row)


def compact_plan(actual: object) -> Record:
    """One contract for shared and generated private pre-submit/result paths."""
    return project_plan(actual)


def publish_before_submit(
    observation: object, *, current_request_path: str | Path, game_launch_receipt: str | Path,
    response_root: str | Path, feed_root: str | Path,
    project_plan: Callable[[object], Record] = compact_plan,
) -> None:
    actual_observation = record(observation)
    context = record(json.loads(Path(current_request_path).read_text(encoding="utf-8-sig")))
    launch = record(json.loads(Path(game_launch_receipt).read_text(encoding="utf-8-sig")))
    sequence = exact_int(context.get("sequence"), "sequence", minimum=1)
    if context.get("tool") != "ck3_auto_turn":
        raise ValueError("pre-submit publication lacks this queue's held auto-turn request")
    actual = record(actual_observation.get("plan"))
    if actual.get("selected_step") != actual_observation.get("selected_step"):
        raise ValueError("actual selected plan is missing")
    plan = record(project_plan(actual))
    if plan.get("selected_step") != actual.get("selected_step"):
        raise ValueError("display projection differs from the actual selected step")
    pid = exact_int(launch.get("pid"), "game pid", minimum=1)
    birth = launch.get("creation_date")
    if not isinstance(birth, str) or not birth:
        raise ValueError("game creation date missing")
    body = {"status": "planned", "plan": plan, "selected_step": actual_observation["selected_step"],
            "snapshot_id": actual_observation.get("snapshot_id"), "revision": actual_observation.get("revision")}
    row: Record = {"ended_at_utc": datetime.now(timezone.utc).isoformat(),
                   "source": "actual GameplayBridgeService.before_submit callback",
                   "game_pid": pid, "game_creation_date": birth,
                   "source_namespace": Path(response_root).resolve().name,
                   "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": sequence},
                   "result": {"is_error": False, "structured_content": body}}
    output = _publish_new(Path(response_root).resolve() / f"{sequence:04d}-0-plan.json", row)
    relay_compact(output, row, feed_root=feed_root)


def error_projection(row: object) -> Record:
    actual = record(row)
    result = maybe_record(actual.get("result"))
    messages = [str(actual["client_error"])[:2048]] if actual.get("client_error") else []
    blocks = result.get("content")
    if isinstance(blocks, list):
        for value in blocks[:3]:
            block = maybe_record(value)
            message = block.get("text")
            if block.get("type") == "text" and isinstance(message, str):
                messages.append(message[:2048])
    return {"request": actual.get("request"), "ended_at_utc": actual.get("ended_at_utc"),
            "source": "compact actual SDK error; original response retained",
            "result": {"is_error": True, "structured_content": {
                "status": "error", "message": "\n".join(messages)[:6144],
                "outcome_verified": False, "original_request_replayed": False}}}
