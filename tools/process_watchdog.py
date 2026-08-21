"""Kill one tracked CK3 process tree if its acceptance runner exits."""

import subprocess
import sys
from pathlib import Path

import win32api
import win32com.client
import win32con
import win32event


def main() -> None:
    parent_pid = int(sys.argv[1])
    ck3_pid_file = Path(sys.argv[2])
    try:
        handle = win32api.OpenProcess(win32con.SYNCHRONIZE, False, parent_pid)
        win32event.WaitForSingleObject(handle, win32event.INFINITE)
    except Exception:
        pass

    pids = []
    try:
        pids.append(int(ck3_pid_file.read_text(encoding="ascii").strip()))
    except (OSError, ValueError):
        try:
            service = win32com.client.GetObject("winmgmts:")
            children = service.ExecQuery(
                "SELECT ProcessId FROM Win32_Process "
                f"WHERE Name='ck3.exe' AND ParentProcessId={parent_pid}"
            )
            pids.extend(int(child.ProcessId) for child in children)
        except Exception:
            pass

    failures = []
    for ck3_pid in sorted(set(pids)):
        result = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(ck3_pid)], capture_output=True
        )
        if result.returncode != 0:
            failures.append(f"{ck3_pid}:{result.returncode}")
    if failures:
        try:
            ck3_pid_file.with_suffix(".watchdog_error").write_text(
                ",".join(failures) + "\n", encoding="ascii"
            )
        except OSError:
            pass


if __name__ == "__main__":
    main()
