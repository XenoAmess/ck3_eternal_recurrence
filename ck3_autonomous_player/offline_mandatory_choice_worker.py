"""Separate-process review of immutable unknown-choice and MCP response files.

No Game, Desktop, OBS, task-bus or live Driver access. It only publishes
unresolved/observed-UI facts; business semantics remain unknown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


PACKAGE = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE))
from xar_autoplayer.mandatory_choice_evidence_v1 import collect_completed  # noqa: E402
from xar_autoplayer.mandatory_choice_offline_analysis_v1 import (  # noqa: E402
    analyze_completed_incident, stable_source_key)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_once(path: Path, value: dict) -> None:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                          indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError(f"immutable review path changed: {path}")


def _later_progress(attempt: Path, before: dict, after: dict) -> dict | None:
    source = before.get("frame_binding")
    if not isinstance(source, dict):
        return None
    launch = attempt / "ROOT-ACTUAL-GAME-LAUNCH.json"
    if not launch.is_file():
        return None
    pid = json.loads(launch.read_text(encoding="utf-8")).get("pid")
    if pid != source.get("game_pid"):
        return None
    after_at = after.get("captured_at_utc")
    for path in reversed(sorted(attempt.glob("p*-responses/*-result.json"))):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(after_at, str) and value.get("ended_at_utc", "") <= after_at:
            break
        envelope = value.get("result")
        if not isinstance(envelope, dict) or envelope.get("is_error") is True:
            continue
        frame = envelope.get("structured_content")
        if (not isinstance(frame, dict)
                or frame.get("actor_character_id") != source.get("actor_character_id")
                or frame.get("episode_run_id") != source.get("episode_run_id")
                or frame.get("connection_generation") != source.get("connection_generation")
                or type(frame.get("date_raw")) is not int
                or frame["date_raw"] <= source.get("date_raw", -1)
                or type(frame.get("native_revision")) is not int
                or frame["native_revision"] <= source.get("native_revision", -1)):
            continue
        return {"source_path": str(path), "source_sha256": _sha(path),
                "json_pointer": ["result", "structured_content"],
                "game_launch_receipt_path": str(launch),
                "game_launch_receipt_sha256": _sha(launch)}
    return None


def review_once(attempt: Path, output: Path) -> list[dict]:
    launch = attempt / "ROOT-ACTUAL-GAME-LAUNCH.json"
    backend = json.loads(launch.read_text(encoding="utf-8")).get("dll_sha256")
    results = []
    for pair in collect_completed(attempt / "state"):
        before_path, after_path = Path(pair["before"]), Path(pair["after"])
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = json.loads(after_path.read_text(encoding="utf-8"))
        dto = before.get("native_window")
        can_promote = (after.get("original_blocking_window_advanced_verified") is True
                       and stable_source_key(dto, backend_sha256=backend) is not None)
        progress = _later_progress(attempt, before, after) if can_promote else None
        review = analyze_completed_incident(
            before, after, backend_sha256=backend, later_progress=progress)
        review.update({"schema": "xar.unknown-mandatory-choice-offline-review/v1",
                       "incident_id": pair["incident_id"],
                       "before_path": pair["before"],
                       "before_sha256": pair["before_sha256"],
                       "after_path": pair["after"],
                       "after_sha256": pair["after_sha256"],
                       "Game_MCP_OBS_calls": 0})
        suffix = progress["source_sha256"][:12] if progress else "no-progress"
        target = output / (pair["incident_id"] + "." + suffix + ".review.json")
        _write_once(target, review)
        if review["status"] == "known_ui_recovery_observed":
            _write_once(output / "known-ui-recovery" / review["source_key"] /
                        (pair["incident_id"] + ".json"), review)
        results.append({"incident_id": pair["incident_id"],
                        "status": review["status"], "review": str(target)})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    args = parser.parse_args()
    if args.follow and (args.stop_file is None or args.poll_seconds <= 0):
        parser.error("follow requires a stop-file and positive poll interval")
    while True:
        results = review_once(args.attempt_root, args.output_dir)
        print(json.dumps({"reviewed": len(results), "statuses": [
            row["status"] for row in results]}, ensure_ascii=False), flush=True)
        if not args.follow or args.stop_file.is_file():
            return
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
