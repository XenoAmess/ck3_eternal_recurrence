"""Finite original-Popen custody for this source-only lane; never runs native code."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MACHINE = "desktop-3fevhd2-1c74096080"
LIB = "C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib"


def write(name: str, value: object) -> None:
    payload = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    used = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    if used + len(payload) > 65536:
        raise RuntimeError("source lane 64KiB ceiling")
    with (ROOT / name).open("xb") as stream:
        stream.write(payload)


def birth(process: subprocess.Popen[bytes]) -> str:
    handle: object = getattr(process, "_handle", None)
    if not isinstance(handle, int) or isinstance(handle, bool):
        raise RuntimeError("original Python process handle")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    c, e, k, u = (wintypes.FILETIME() for _ in range(4))
    if not kernel.GetProcessTimes(wintypes.HANDLE(handle), ctypes.byref(c), ctypes.byref(e),
                                  ctypes.byref(k), ctypes.byref(u)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((c.dwHighDateTime << 32) | c.dwLowDateTime)


def run(label: str, argv: list[str]) -> int:
    env = os.environ.copy()
    env.update(PYTHONPATH=str(ROOT) + os.pathsep + LIB, MYPYPATH=str(ROOT),
               PYTHONDONTWRITEBYTECODE="1", TEMP=str(ROOT / "tmp"), TMP=str(ROOT / "tmp"))
    write(label + ".INTENT.json", dict(machine_id=MACHINE, argv=argv,
          observed_at_utc=datetime.now(timezone.utc).isoformat(), no_native_Game=True))
    process: subprocess.Popen[bytes] = subprocess.Popen(argv, cwd=ROOT, env=env,
          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    created: str | None = None
    identity_error: str | None = None
    try:
        try:
            created = birth(process)
        except BaseException as exc:
            identity_error = type(exc).__name__ + ": " + str(exc)
        out, err = process.communicate()
    finally:
        code = process.wait()
    streams: dict[str, object] = {}
    for key, payload in (("stdout", out), ("stderr", err)):
        if len(payload) > 8192:
            raise RuntimeError("bounded check output exceeded; actual Python wait retained")
        name = label + "." + key + ".log"
        with (ROOT / name).open("xb") as stream:
            stream.write(payload)
        streams[key] = dict(path=str(ROOT / name), bytes=len(payload),
                            sha256=hashlib.sha256(payload).hexdigest())
    write(label + ".ORIGINAL-WAIT.json", dict(machine_id=MACHINE,
          observed_at_utc=datetime.now(timezone.utc).isoformat(), argv=argv,
          pid=process.pid, created=created, identity_error=identity_error,
          original_Popen=True, original_wait=True, returncode=code, streams=streams,
          SDK_native_Game=False))
    return code


def main() -> int:
    (ROOT / "tmp").mkdir(exist_ok=True)
    focused = run("focused-a01", [sys.executable, "-B", "-X", "utf8", "-m", "unittest",
                                  "-v", "test_generic_applied_net"])
    strict = run("mypy-a01", [sys.executable, "-B", "-X", "utf8", "-m", "mypy",
        "--strict", "--no-incremental", "--cache-dir=nul",
        str(ROOT / "war_generic_applied_net_12004.py"),
        str(ROOT / "test_generic_applied_net.py"), str(ROOT / "run_checks.py")])
    print(json.dumps(dict(focused=focused, strict=strict)))
    return 0 if focused == strict == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
