"""One authorized absolute-original-manifest dry-run preview, never a build."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import win32file

REPO = Path(__file__).resolve().parents[2]
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
OUT = REPO/"docs/ck3-native-ai/evidence/native30-fixture07-absolute-manifest-preview-2026-10-20.json"
assert not OUT.exists(), "preserve preview; no automatic repeat"
inventory = json.loads((REPO/"docs/ck3-native-ai/evidence/native30-existing-config-output-inventory-2026-10-19.json").read_bytes())
tool = inventory["tool_pins"]["ninja"]
manifest = R/"build/build.ninja"
handles = []
try:
    for path in (tool["path"], str(manifest)):
        handles.append(win32file.CreateFile(path, 0x80000000, 1, None, 3, 0x80, None))
    assert hashlib.sha256(Path(tool["path"]).read_bytes()).hexdigest() == tool["sha256"]
    before = hashlib.sha256(manifest.read_bytes()).hexdigest()
    argv = [tool["path"], "-C", str(R/"build"), "-f", str(manifest), "-n", "-d", "explain",
            "xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol"]
    start = datetime.now(timezone.utc).isoformat()
    process = subprocess.Popen(argv, cwd=R/"build", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    tail, total = bytearray(), [0]
    def drain():
        while chunk := process.stdout.read(1024):
            total[0] += len(chunk)
            tail.extend(chunk)
            if len(tail) > 4096: del tail[:-4096]
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    forced = False
    try: code = process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        forced = True
        process.kill()
        code = process.wait(timeout=5)
    reader.join(timeout=5)
    assert not reader.is_alive()
    after = hashlib.sha256(manifest.read_bytes()).hexdigest()
    result = {"machine_id": "xenoamess-full-tower-eb9d2c1186", "start_utc": start,
        "end_utc": datetime.now(timezone.utc).isoformat(), "argv": argv, "cwd": str(R/"build"),
        "tool": tool, "owned_pid": process.pid, "exit_code": code, "forced_exact_child": forced,
        "output_total_bytes": total[0], "retained_tail": tail.decode("utf-8", errors="backslashreplace"),
        "manifest": {"path": str(manifest), "bytes": manifest.stat().st_size, "before_SHA": before, "after_SHA": after},
        "scope": "Authorized absolute original -f preview only; no snapshot has been created or qualified.",
        "R_Task_CMake_compiler_Game_writes": 0, "future_writes": 0}
    raw = (json.dumps(result, indent=2)+"\n").encode()
    assert len(raw) <= 8192
    with OUT.open("xb") as stream: stream.write(raw)
    print(raw.decode())
finally:
    for handle in handles: handle.Close()
