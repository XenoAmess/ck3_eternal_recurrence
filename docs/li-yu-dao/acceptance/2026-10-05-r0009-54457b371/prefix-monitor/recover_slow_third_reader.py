"""Stop only this observer's exact slow Python worker; retain partial 003."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import psutil

ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "slow-third-reader-recovery-001"
DESTINATION.mkdir()
snapshot_path = (ROOT / "snapshot.py").resolve()
matches = []
for process in psutil.process_iter(attrs=["pid", "name"]):
    if process.info["name"].lower() != "python.exe":
        continue
    try:
        argv = process.cmdline()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
    paths = [Path(arg).resolve() for arg in argv if arg.endswith("snapshot.py")]
    if snapshot_path in paths and "after-sign-and-first-join-prefix-003" in argv:
        if "--snapshot-key" not in argv or argv[argv.index("--snapshot-key") + 1] != "after-sign-and-first-join-prefix-003":
            raise AssertionError("Observer argument identity failed")
        matches.append((process, argv))
if len(matches) > 1:
    raise AssertionError("Ambiguous worker identity; no process action")
receipt = {"time_utc": datetime.now(timezone.utc).isoformat(), "scope": "Exact snapshot.py + 003 key only",
           "game_pid_excluded": 20264, "matched_workers": len(matches), "old_artifacts_deleted": False,
           "old_partial_raw_error_sha256": hashlib.sha256((ROOT / "after-sign-and-first-join-prefix-003/raw-prefix/error.log").read_bytes()).hexdigest()}
if matches:
    process, argv = matches[0]
    if process.pid in {20264, psutil.Process().pid}:
        raise AssertionError("Refuse game/self process")
    receipt.update({"worker_pid": process.pid, "worker_create_time": process.create_time(), "worker_argv": argv})
    with (DESTINATION / "BEFORE.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    process.terminate()
    receipt["worker_exit_code"] = process.wait(timeout=10)
    receipt["exact_worker_terminated"] = True
else:
    receipt["exact_worker_terminated"] = False
with (DESTINATION / "RECEIPT.json").open("x", encoding="utf-8") as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
