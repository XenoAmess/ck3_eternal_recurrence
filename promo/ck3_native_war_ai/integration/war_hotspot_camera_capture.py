"""Follow a native war hotspot through the same selector used by the agent.

The running capture session owns the MCP connection. This helper submits one
presentation-only request into that session and preserves its exact response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
from xar_autoplayer.bridge.war_hotspot_camera import (  # noqa: E402
    LandedProvinceIndex,
    follow_war_hotspot,
)
from xar_autoplayer.bridge.camera_cursor_parking import park_foreground_ck3_cursor  # noqa: E402


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


class CaptureCameraService:
    def __init__(self, request_dir: Path, name: str, timeout_seconds: float) -> None:
        self.request_dir = request_dir
        self.response_dir = request_dir.parent / (request_dir.name + "-responses")
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.request_path: Path | None = None
        self.response_path: Path | None = None

    def center_map_on_landed_title_v1(
        self, title_key: str, *, expected_revision: int
    ) -> dict[str, object]:
        if not self.request_dir.is_dir() or not self.response_dir.is_dir():
            raise RuntimeError("capture session request service is not ready")
        request = self.request_dir / f"{self.name}-camera.json"
        response = self.response_dir / request.name
        temp = self.request_dir.parent / f"{self.name}-camera.pending"
        if request.exists() or response.exists() or temp.exists():
            raise FileExistsError(f"camera request already exists: {request}")
        payload = {
            "action": "mcp", "tool": "ck3_center_map_on_landed_title_v1",
            "arguments": {"title_key": title_key,
                          "expected_revision": expected_revision},
        }
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False)
            stream.write("\n")
        os.replace(temp, request)
        self.request_path = request
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if response.is_file():
                try:
                    row = json.loads(response.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    time.sleep(0.1)
                    continue
                self.response_path = response
                if row.get("result") != "CALL_COMPLETED":
                    raise RuntimeError(f"camera MCP request failed: {row.get('error')}")
                body = row.get("body")
                if not isinstance(body, dict):
                    raise ValueError("camera MCP response has no result object")
                return body
            time.sleep(0.25)
        raise TimeoutError(f"camera MCP response timed out: {response}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, type=Path)
    parser.add_argument("--request-dir", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=120)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.name):
        parser.error("--name must contain only letters, numbers, hyphen or underscore")
    raw = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    snapshot = raw.get("body") if isinstance(raw, dict) and isinstance(raw.get("body"), dict) else raw
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a JSON object or an MCP body")
    index = LandedProvinceIndex.from_game_dir(args.game_dir)
    service = CaptureCameraService(args.request_dir, args.name, args.timeout_seconds)
    result = follow_war_hotspot(
        service, snapshot, index, park_cursor=park_foreground_ck3_cursor
    )
    witness = None
    if args.screenshot is not None and result["status"] in {"centered", "already_centered"}:
        import pyautogui
        if args.screenshot.exists():
            raise FileExistsError(args.screenshot)
        pyautogui.screenshot().save(args.screenshot)
        witness = identity(args.screenshot)
    record = {
        "schema": "ck3.native-war-hotspot-camera-capture.v1",
        "snapshot": identity(args.snapshot),
        "mapped_land_provinces": len(index.barony_by_province),
        "camera_follow": result,
        "request": identity(service.request_path) if service.request_path else None,
        "response": identity(service.response_path) if service.response_path else None,
        "desktop_witness": witness,
    }
    if args.output.exists():
        raise FileExistsError(args.output)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "hotspot": result["hotspot"],
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
