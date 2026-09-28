"""Read-only H3911 receiver diagnostics for preserved external attempts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from h3911_readiness_gate import probe_postread


ROOT = Path(r"D:\ck3-research-artifacts\r0321-h3911-receiver-20260928")
for number in (1, 2):
    attempt = ROOT / f"attempt-{number}-h3911-readonly-no-launch"
    live = attempt / "live-h3911-readonly-v1"
    logs = attempt / "state" / "profile" / "logs"
    print(f"\nATTEMPT {number}")
    launch_plan = json.loads((live / "launch-plan.json").read_text(encoding="utf-8"))
    coldload = probe_postread(
        attempt, logs / "debug.log",
        datetime.fromisoformat(launch_plan["started_at_utc"]),
    )
    print("coldload_log_probe", coldload)
    for name in ("debug.log", "error.log", "game.log", "setup.log"):
        path = logs / name
        if not path.exists():
            continue
        rows = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        changed = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        print(f"\n{name} bytes={path.stat().st_size} lines={len(rows)} mtime_utc={changed}")
        for line in rows[-18:]:
            print(line[:250])
    snapshots = sorted(live.glob("readiness-???.json"))
    print(f"\nreadiness_count={len(snapshots)}")
    for path in (snapshots[0], snapshots[-1]) if snapshots else ():
        value = json.loads(path.read_text(encoding="utf-8"))
        print(path.name, datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
              "isError", value.get("isError"), "text", str(value.get("content", ""))[:250])
    for name in ("session-exit.json", "failure.json"):
        path = live / name
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            print(name, {k: value.get(k) for k in ("returncode", "type", "message", "at_utc", "gameplay_action_submitted")})
