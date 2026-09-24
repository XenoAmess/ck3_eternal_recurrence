"""Record a native battle while recentering on every observed war hotspot.

This is a capture attempt, not an edited video or a battle-model signoff.
The existing capture_session.py owns CK3 and its MCP connection.
"""

from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import pyautogui

from battle_frame_gate import battle_marker_score
from war_hotspot_camera_capture import CaptureCameraService, identity
from xar_autoplayer.bridge.war_hotspot_camera import (
    LandedProvinceIndex,
    follow_war_hotspot,
    select_war_hotspot,
)
from xar_autoplayer.bridge.camera_cursor_parking import park_foreground_ck3_cursor


def submit(request_dir: Path, name: str, tool: str, arguments: dict | None = None) -> tuple[dict, Path]:
    response_dir = request_dir.parent / (request_dir.name + "-responses")
    request = request_dir / f"{name}.json"
    response = response_dir / request.name
    temp = request_dir.parent / f"{name}.pending"
    if any(path.exists() for path in (request, response, temp)):
        raise FileExistsError(request)
    with temp.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"action": "mcp", "tool": tool, "arguments": arguments or {}}, stream)
        stream.write("\n")
    os.replace(temp, request)
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        if response.is_file():
            try:
                row = json.loads(response.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.1)
                continue
            if row.get("result") != "CALL_COMPLETED":
                raise RuntimeError(f"{name}: {row.get('error')}")
            body = row.get("body")
            if not isinstance(body, dict):
                raise ValueError(f"{name} has no MCP result object")
            return body, response
        time.sleep(0.25)
    raise TimeoutError(response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--max-days", type=int, default=34)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--attempt-key", default="gameplay-hotspot-follow")
    parser.add_argument("--hold-seconds", type=float, default=5)
    parser.add_argument("--expected-first-province", type=int)
    parser.add_argument("--expected-first-date", type=int)
    parser.add_argument("--visibility-reference", required=True, type=Path)
    parser.add_argument("--minimum-marker-score", type=float, default=0.75)
    args = parser.parse_args()
    if not (1 <= args.start_index <= args.max_days <= 90 and 0 <= args.hold_seconds <= 120):
        parser.error("max-days/hold-seconds out of bounded range")
    if not args.attempt_key or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.attempt_key):
        parser.error("attempt-key must contain only letters, numbers, hyphen or underscore")
    if not (0.0 < args.minimum_marker_score <= 1.0):
        parser.error("minimum-marker-score must be in (0, 1]")
    if not args.visibility_reference.is_file():
        raise FileNotFoundError(args.visibility_reference)
    request_dir = args.run_dir / "ck3-output" / "interactive-requests"
    if not request_dir.is_dir():
        raise RuntimeError("capture session is not accepting requests")
    index = LandedProvinceIndex.from_game_dir(args.game_dir)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise FileNotFoundError("ffmpeg")
    footage = args.run_dir / f"{args.attempt_key}.mkv"
    log_path = args.run_dir / f"{args.attempt_key}-ffmpeg.log"
    journal_path = args.run_dir / f"{args.attempt_key}-journal.jsonl"
    if any(path.exists() for path in (footage, log_path, journal_path)):
        raise FileExistsError("capture attempt files already exist")
    command = [ffmpeg, "-n", "-hide_banner", "-loglevel", "warning",
               "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0",
               "-i", "desktop", "-c:v", "libx264", "-preset", "ultrafast",
               "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(footage)]
    (args.run_dir / f"{args.attempt_key}-command.json").write_text(
        json.dumps(command, indent=2), encoding="utf-8"
    )
    with log_path.open("xb") as ffmpeg_log, journal_path.open("x", encoding="utf-8", newline="\n") as journal:
        recorder = subprocess.Popen(command, stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL, stderr=ffmpeg_log)
        try:
            time.sleep(2)
            if recorder.poll() is not None:
                raise RuntimeError("ffmpeg exited before first battle frame")
            for day in range(args.start_index, args.max_days + 1):
                tag = f"{args.attempt_key}-d{day:02d}"
                snapshot, snapshot_response = submit(request_dir, tag + "-snapshot", "ck3_take_snapshot")
                if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
                    raise RuntimeError(f"{tag}: CK3 is not paused and map-ready")
                selected = select_war_hotspot(snapshot, index)
                if not isinstance(selected, dict) or selected.get("reason") != "battle":
                    row = {"day_index": day, "status": "battle_no_longer_active",
                           "snapshot": identity(snapshot_response),
                           "next_war_hotspot": selected,
                           "camera_preserved_at_last_battle_position": True}
                    journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                    journal.flush()
                    time.sleep(args.hold_seconds)
                    break
                camera_service = CaptureCameraService(request_dir, tag, 120)
                followed = follow_war_hotspot(
                    camera_service, snapshot, index,
                    park_cursor=park_foreground_ck3_cursor,
                )
                hotspot = followed.get("hotspot")
                if day == args.start_index:
                    if args.expected_first_date is not None and snapshot.get("date_raw") != args.expected_first_date:
                        raise ValueError("first battle date differs from requested checkpoint")
                    if args.expected_first_province is not None and (
                        not isinstance(hotspot, dict) or hotspot.get("province_id") != args.expected_first_province
                    ):
                        raise ValueError("first battle province differs from requested checkpoint")
                screenshot = args.run_dir / f"{tag}-centered.png"
                pyautogui.screenshot().save(screenshot)
                visibility = battle_marker_score(args.visibility_reference, screenshot)
                row = {
                    "day_index": day,
                    "status": ("centered_and_visible" if visibility["score"] >= args.minimum_marker_score
                               else "camera_pixel_red"),
                    "snapshot": identity(snapshot_response),
                    "date_raw": snapshot.get("date_raw"),
                    "revision": snapshot.get("revision"),
                    "hotspot": hotspot,
                    "cursor_park": followed.get("cursor_park"),
                    "camera_response": identity(camera_service.response_path),
                    "camera_postcondition_verified": (
                        followed["camera_receipt"]["camera_center"]["postcondition_verified"]
                    ),
                    "desktop_witness": identity(screenshot),
                    "battle_marker_visibility": visibility,
                    "minimum_marker_score": args.minimum_marker_score,
                }
                journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                journal.flush()
                if row["status"] == "camera_pixel_red":
                    raise RuntimeError(f"{tag}: battle marker absent after native camera command")
                print(json.dumps({"day": day, "date_raw": row["date_raw"],
                                  "hotspot": hotspot, "camera": followed["status"]},
                                 ensure_ascii=False), flush=True)
                time.sleep(args.hold_seconds)
                held_frame = args.run_dir / f"{tag}-held.png"
                pyautogui.screenshot().save(held_frame)
                held_visibility = battle_marker_score(args.visibility_reference, held_frame)
                held = {
                    "day_index": day,
                    "status": ("held_frame_visible" if held_visibility["score"] >= args.minimum_marker_score
                               else "held_frame_camera_red"),
                    "desktop_witness": identity(held_frame),
                    "battle_marker_visibility": held_visibility,
                }
                journal.write(json.dumps(held, ensure_ascii=False) + "\n")
                journal.flush()
                if held["status"] == "held_frame_camera_red":
                    raise RuntimeError(f"{tag}: battle marker drifted out during the held shot")
                if recorder.poll() is not None:
                    raise RuntimeError(f"ffmpeg exited during {tag}")
                advance, advance_response = submit(
                    request_dir, tag + "-advance", "ck3_execute_step",
                    {"step": "life-advance", "expected_revision": snapshot["revision"]},
                )
                if advance.get("starting_date_raw") != snapshot["date_raw"] or (
                    advance.get("ending_date_raw") != snapshot["date_raw"] + 24
                ):
                    raise ValueError(f"{tag}: life-advance did not move one native day")
                journal.write(json.dumps({
                    "day_index": day, "status": "advanced_one_day",
                    "advance_response": identity(advance_response),
                    "ending_date_raw": advance["ending_date_raw"],
                }, ensure_ascii=False) + "\n")
                journal.flush()
            else:
                raise RuntimeError("battle did not terminate within max-days")
        finally:
            if recorder.poll() is None and recorder.stdin is not None:
                recorder.stdin.write(b"q\n")
                recorder.stdin.flush()
                recorder.stdin.close()
            exit_code = recorder.wait(timeout=45)
            print(json.dumps({"ffmpeg_exit_code": exit_code,
                              "footage": identity(footage) if footage.exists() else None}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
