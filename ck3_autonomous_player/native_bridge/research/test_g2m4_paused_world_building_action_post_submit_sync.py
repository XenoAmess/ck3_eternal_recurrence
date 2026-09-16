"""Focused no-launch tests for post-submit paused-frame synchronization."""

from __future__ import annotations

import ast
from pathlib import Path

from run_g2m4_paused_world_building_action import (
    _wait_for_newer_paused_frame,
)


HERE = Path(__file__).resolve().parent


def snapshot(revision: int, *, paused: bool = True, date_raw: int = 53178312,
             actor: int = 29829) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "native_revision": revision,
        "date_raw": date_raw,
        "paused": paused,
        "map_ready": True,
        "played_character": {"character_id": actor, "alive": True},
        "active_wars": [],
        "player_armies": [],
        "active_event": None,
        "pending_character_interaction": None,
    }


class State:
    def __init__(self, frames: list[dict[str, object]]) -> None:
        self.frames = frames
        self.index = 0

    def semantic_snapshot(self) -> dict[str, object]:
        frame = self.frames[min(self.index, len(self.frames) - 1)]
        self.index += 1
        return frame


class Driver:
    def __init__(self, frames: list[dict[str, object]]) -> None:
        self.state = State(frames)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    before = {
        "native_revision": 3,
        "date_raw": 53178312,
        "played_character_id": 29829,
    }
    frame, last, issue = _wait_for_newer_paused_frame(
        Driver([snapshot(3), snapshot(3), snapshot(4)]),
        before,
        1.0,
        poll_interval_seconds=0.0,
    )
    require(issue is None and frame is not None and frame["native_revision"] == 4,
            "stale revision was not skipped")
    require(last == frame, "accepted frame is not reported")

    frame, _, issue = _wait_for_newer_paused_frame(
        Driver([snapshot(4, paused=False), snapshot(4)]),
        before,
        1.0,
        poll_interval_seconds=0.0,
    )
    require(issue is None and frame is not None and frame["paused"] is True,
            "newer unpaused frame was not allowed to settle")

    frame, _, issue = _wait_for_newer_paused_frame(
        Driver([snapshot(4, actor=999)]),
        before,
        1.0,
        poll_interval_seconds=0.0,
    )
    require(frame is None and issue == "post_action_frame_identity_changed_keep_pending",
            "actor drift did not stop pending action")

    frame, _, issue = _wait_for_newer_paused_frame(
        Driver([snapshot(3)]),
        before,
        0.0,
        poll_interval_seconds=0.0,
    )
    require(frame is None and issue == "newer_paused_frame_timeout_keep_pending",
            "stale timeout did not preserve pending receipt")

    source_path = HERE / "run_g2m4_paused_world_building_action.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source)
    require(source.count("driver, ACTION_STEP,") == 1,
            "private action acquired a retry path")
    require("material_frame[\"native_revision\"]" in source,
            "material read is not bound to the newer frame")
    print("GREEN post-submit paused-frame sync; one action submit; no CK3 launch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
